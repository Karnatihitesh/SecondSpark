from datetime import datetime
from app.models.user import db


class Transaction(db.Model):
    """Stores every payment between a helper and project owner, with 2% platform commission."""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)

    # Relationships
    project_id  = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    payer_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)   # helper paying
    payee_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)   # project owner receiving

    # Financial amounts (INR — all stored in paisa-equivalent floats)
    amount_inr      = db.Column(db.Float, nullable=False)       # full agreed repair cost
    commission_inr  = db.Column(db.Float, nullable=False)       # 2% platform fee to admin
    net_amount_inr  = db.Column(db.Float, nullable=False)       # 98% credited to payee

    # Payment details
    payment_method      = db.Column(db.String(30), default='UPI')   # 'gpay', 'phonepe', 'bhim', 'paytm', 'upi'
    gateway             = db.Column(db.String(20), default='gateway1')  # 'gateway1' | 'gateway2'
    upi_vpa             = db.Column(db.String(120), nullable=True)      # payer's UPI VPA
    upi_transaction_id  = db.Column(db.String(120), nullable=True)      # final UTR from gateway
    order_id            = db.Column(db.String(64), nullable=True, unique=True)  # internal order ID

    # Lifecycle
    status      = db.Column(db.String(20), default='Pending', nullable=False, index=True)
    # Pending → Initiated → Completed | Failed | Refunded

    notes       = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ORM back-refs
    project = db.relationship('Project', backref=db.backref('transactions', lazy='dynamic'))
    payer   = db.relationship('User', foreign_keys=[payer_id], backref=db.backref('payments_made', lazy='dynamic'))
    payee   = db.relationship('User', foreign_keys=[payee_id], backref=db.backref('payments_received', lazy='dynamic'))

    @classmethod
    def compute_split(cls, amount_inr: float):
        """Return (commission, net) tuple for a given amount."""
        commission = round(amount_inr * 0.02, 2)
        net = round(amount_inr - commission, 2)
        return commission, net

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'project_id': self.project_id,
            'amount_inr': self.amount_inr,
            'commission_inr': self.commission_inr,
            'net_amount_inr': self.net_amount_inr,
            'payment_method': self.payment_method,
            'gateway': self.gateway,
            'upi_transaction_id': self.upi_transaction_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Transaction #{self.id} ₹{self.amount_inr} [{self.status}]>'
