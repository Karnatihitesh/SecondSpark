"""
SecondSpark Payment Routes
──────────────────────────
Two-gateway UPI payment flow with 2% platform commission.

Gateway 1 — Primary (GPay / PhonePe / BHIM / any UPI)
Gateway 2 — Fallback (Paytm / other UPI apps)

Flow:
  1. User clicks "Agree & Pay" on a project detail page
  2. GET /payments/checkout/<project_id>  — shows terms + payment form
  3. POST /payments/initiate              — validates amount, creates order, shows QR/UPI
  4. POST /payments/confirm               — user submits UTR, marks complete
  5. GET /payments/success/<order_id>     — success page
  6. GET /payments/history                — user's transaction history
"""

import uuid
import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.models.user import db, User
from app.models.project import Project
from app.models.transaction import Transaction
from app.services.auth_service import get_current_user, login_required

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

# ── Constants ─────────────────────────────────────────────────────────────────
PLATFORM_COMMISSION_RATE = 0.02     # 2% to admin
MIN_AMOUNT_INR           = 500.0    # ₹500 minimum
ADMIN_UPI_G1             = 'secondspark@oksbi'       # Gateway 1 — primary
ADMIN_UPI_G2             = 'secondspark@ybl'         # Gateway 2 — fallback


def _generate_order_id() -> str:
    return 'SS' + uuid.uuid4().hex[:12].upper()


# ── 1. Checkout Page ──────────────────────────────────────────────────────────
@payments_bp.route('/checkout/<int:project_id>', methods=['GET', 'POST'])
@login_required
def checkout(project_id):
    user = get_current_user()
    project = Project.query.get_or_404(project_id)

    # Project owner cannot pay themselves
    if project.user_id == user.id:
        flash('You cannot initiate payment for your own project.', 'danger')
        return redirect(url_for('projects.details', id=project.id))

    # Use project budget as default amount; enforce minimum
    default_amount = max(project.budget or 0.0, MIN_AMOUNT_INR)
    commission, net = Transaction.compute_split(default_amount)

    return render_template(
        'payment_checkout.html',
        project=project,
        default_amount=default_amount,
        commission=commission,
        net=net,
        min_amount=MIN_AMOUNT_INR,
        admin_upi_g1=ADMIN_UPI_G1,
        admin_upi_g2=ADMIN_UPI_G2,
    )


# ── 2. Initiate — create order & show UPI QR ──────────────────────────────────
@payments_bp.route('/initiate', methods=['POST'])
@login_required
def initiate():
    user = get_current_user()

    project_id  = request.form.get('project_id', type=int)
    amount_raw  = request.form.get('amount', type=float)
    gateway     = request.form.get('gateway', 'gateway1')
    agreed      = request.form.get('agreed')

    if not agreed:
        flash('You must agree to the platform terms before proceeding.', 'danger')
        return redirect(url_for('payments.checkout', project_id=project_id))

    project = Project.query.get_or_404(project_id)

    # ── Validations ───────────────────────────────────────────────────────────
    if amount_raw is None or amount_raw < MIN_AMOUNT_INR:
        flash(f'Minimum repair cost is ₹{MIN_AMOUNT_INR:,.0f}. Please enter a valid amount.', 'danger')
        return redirect(url_for('payments.checkout', project_id=project_id))

    commission, net = Transaction.compute_split(amount_raw)
    order_id = _generate_order_id()
    admin_upi = ADMIN_UPI_G1 if gateway == 'gateway1' else ADMIN_UPI_G2

    # Build UPI deep-link URL (works on mobile for GPay / PhonePe / BHIM)
    upi_url = (
        f"upi://pay?pa={admin_upi}"
        f"&pn=SecondSpark"
        f"&am={amount_raw:.2f}"
        f"&cu=INR"
        f"&tn=SecondSpark-{order_id}"
        f"&tr={order_id}"
    )

    # Persist pending transaction
    txn = Transaction(
        project_id=project_id,
        payer_id=user.id,
        payee_id=project.user_id,
        amount_inr=amount_raw,
        commission_inr=commission,
        net_amount_inr=net,
        gateway=gateway,
        order_id=order_id,
        status='Initiated'
    )
    db.session.add(txn)
    db.session.commit()

    # Store order_id in session for confirm step
    session['pending_order_id'] = order_id

    return render_template(
        'payment_upi.html',
        project=project,
        txn=txn,
        upi_url=upi_url,
        admin_upi=admin_upi,
        order_id=order_id,
        gateway=gateway,
    )


# ── 3. Confirm — user submits UTR number ──────────────────────────────────────
@payments_bp.route('/confirm', methods=['POST'])
@login_required
def confirm():
    user = get_current_user()
    order_id = request.form.get('order_id', '').strip()
    utr      = request.form.get('utr', '').strip()

    # Basic UTR/transaction ID validation (12 alphanumeric)
    if not re.match(r'^[A-Za-z0-9]{8,50}$', utr):
        flash('Please enter a valid UPI Transaction ID / UTR number.', 'danger')
        return redirect(url_for('payments.history'))

    txn = Transaction.query.filter_by(order_id=order_id, payer_id=user.id).first_or_404()

    if txn.status == 'Completed':
        flash('This transaction has already been confirmed.', 'info')
        return redirect(url_for('payments.success', order_id=order_id))

    txn.upi_transaction_id = utr
    txn.status = 'Completed'
    txn.updated_at = datetime.utcnow()
    db.session.commit()

    # Clear pending session
    session.pop('pending_order_id', None)

    flash('🎉 Payment confirmed successfully! The project owner will be notified.', 'success')
    return redirect(url_for('payments.success', order_id=order_id))


# ── 4. Success page ───────────────────────────────────────────────────────────
@payments_bp.route('/success/<order_id>')
@login_required
def success(order_id):
    user = get_current_user()
    txn  = Transaction.query.filter_by(order_id=order_id).first_or_404()
    return render_template('payment_success.html', txn=txn, project=txn.project)


# ── 5. Transaction History ────────────────────────────────────────────────────
@payments_bp.route('/history')
@login_required
def history():
    user = get_current_user()
    made     = Transaction.query.filter_by(payer_id=user.id).order_by(Transaction.created_at.desc()).all()
    received = Transaction.query.filter_by(payee_id=user.id).order_by(Transaction.created_at.desc()).all()
    return render_template('payment_history.html', made=made, received=received)


# ── 6. AJAX: recalculate commission preview ───────────────────────────────────
@payments_bp.route('/api/calc', methods=['POST'])
@login_required
def calc_commission():
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get('amount', 0))
        if amount < MIN_AMOUNT_INR:
            return jsonify({'error': f'Minimum ₹{MIN_AMOUNT_INR:,.0f}'}), 400
        commission, net = Transaction.compute_split(amount)
        return jsonify({
            'amount': amount,
            'commission': commission,
            'commission_pct': '2%',
            'net': net,
        })
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount'}), 400
