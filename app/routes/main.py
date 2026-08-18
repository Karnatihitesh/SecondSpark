from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models.user import db, User
from app.models.project import Project
from app.models.category import Category
from app.models.review import Review
from app.models.contact import ContactMessage
from app.services.notification_service import create_notification

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    # Fetch featured and latest projects for home page
    featured_projects = Project.query.filter_by(is_featured=True).order_by(Project.created_at.desc()).limit(6).all()
    if not featured_projects:
        # Fallback to recent open projects if none flagged as featured
        featured_projects = Project.query.filter_by(status='Open').order_by(Project.created_at.desc()).limit(6).all()

    latest_projects = Project.query.order_by(Project.created_at.desc()).limit(6).all()
    categories = Category.query.order_by(Category.name.asc()).all()

    # Dynamic platform statistics
    stats = {
        'total_projects': Project.query.count(),
        'completed_projects': Project.query.filter_by(status='Completed').count(),
        'active_collaborators': User.query.filter_by(is_active=True).count(),
        'categories_count': Category.query.count()
    }

    # Latest positive reviews for success stories
    success_reviews = Review.query.filter(Review.rating >= 4).order_by(Review.created_at.desc()).limit(3).all()

    return render_template(
        'home.html',
        featured_projects=featured_projects,
        latest_projects=latest_projects,
        categories=categories,
        stats=stats,
        success_reviews=success_reviews
    )


@main_bp.route('/about')
def about():
    team_members = [
        {
            'name': 'Karnati Hitesh',
            'role': 'Team Lead & Full-Stack Integration',
            'bio': 'Architecting the full-stack system, database design, and end-to-end platform workflows. Contact: karnatihitesh@gmail.com / +91 9490682602',
            'initials': 'KH'
        },
        {
            'name': 'Sadineni Mrudul',
            'role': 'Frontend Development',
            'bio': 'Designing responsive glassmorphism UI, interactive components, and smooth UX states.',
            'initials': 'SM'
        },
        {
            'name': 'Annepalli Jashwanth Reddy',
            'role': 'Authentication & Backend',
            'bio': 'Implementing secure authentication, session management, and backend REST APIs.',
            'initials': 'AJ'
        },
        {
            'name': 'Siripanga Manikumar',
            'role': 'Project Management Module',
            'bio': 'Developing project upload lifecycle, multi-criteria filtering, and status workflows.',
            'initials': 'MK'
        },
        {
            'name': 'Nandala Supriya',
            'role': 'Communication Module',
            'bio': 'Building real-time messaging, conversation threads, and notification pipelines.',
            'initials': 'NS'
        },
        {
            'name': 'Mamidi Vydhika',
            'role': 'Testing & Documentation',
            'bio': 'Ensuring quality assurance, end-to-end integration testing, and API documentation.',
            'initials': 'MV'
        }
    ]
    return render_template('about.html', team_members=team_members)



@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not subject or not message:
            flash('Please fill in all fields before sending your message.', 'danger')
            return render_template('contact.html', form_data=request.form)

        try:
            contact_msg = ContactMessage(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            db.session.add(contact_msg)
            db.session.commit()
            flash('Thank you! Your message has been sent successfully. We will get back to you shortly.', 'success')
            return redirect(url_for('main.contact'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while sending your message. Please try again.', 'danger')

    return render_template('contact.html', form_data={})


@main_bp.route('/how-it-works')
def how_it_works():
    return render_template('home.html', scroll_to='how-it-works')
