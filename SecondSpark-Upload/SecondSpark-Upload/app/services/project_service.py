import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy import or_, and_
from app.models.user import db
from app.models.project import Project, ProjectImage, ProjectDocument
from app.models.category import Category


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, subfolder='projects', is_image=True):
    """
    Safely save an uploaded file with randomized secure filename.
    Returns the web-accessible static URL.
    """
    if not file or file.filename == '':
        return None

    allowed_exts = current_app.config['ALLOWED_IMAGE_EXTENSIONS'] if is_image else current_app.config['ALLOWED_DOC_EXTENSIONS']
    
    if not allowed_file(file.filename, allowed_exts):
        return None

    orig_name = secure_filename(file.filename)
    ext = orig_name.rsplit('.', 1)[1].lower() if '.' in orig_name else ('png' if is_image else 'pdf')
    unique_name = f"{uuid.uuid4().hex[:12]}_{int(os.times().elapsed * 100)}.{ext}"
    
    target_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, unique_name)
    file.save(file_path)
    
    # Return web path relative to static
    return f"/static/uploads/{subfolder}/{unique_name}"


def build_project_query(search=None, category_slug=None, status=None, min_budget=None, max_budget=None, location=None, skill=None, sort='newest'):
    """
    Constructs a SQLAlchemy query with all filters applied.
    """
    query = Project.query.join(Category, isouter=True)

    # Search in title, short_summary, description, required_skills, problems_faults
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Project.title.ilike(term),
                Project.short_summary.ilike(term),
                Project.description.ilike(term),
                Project.required_skills.ilike(term),
                Project.problems_faults.ilike(term),
                Category.name.ilike(term)
            )
        )

    # Category filter
    if category_slug and category_slug != 'all':
        query = query.filter(Category.slug == category_slug)

    # Status filter
    if status and status != 'all':
        query = query.filter(Project.status == status)

    # Budget range
    if min_budget is not None and min_budget != '':
        try:
            query = query.filter(Project.budget >= float(min_budget))
        except ValueError:
            pass

    if max_budget is not None and max_budget != '':
        try:
            query = query.filter(Project.budget <= float(max_budget))
        except ValueError:
            pass

    # Location
    if location and location.strip():
        query = query.filter(Project.location.ilike(f"%{location.strip()}%"))

    # Skill filter
    if skill and skill.strip():
        query = query.filter(Project.required_skills.ilike(f"%{skill.strip()}%"))

    # Sorting
    if sort == 'oldest':
        query = query.order_by(Project.created_at.asc())
    elif sort == 'budget_high':
        query = query.order_by(Project.budget.desc())
    elif sort == 'budget_low':
        query = query.order_by(Project.budget.asc())
    elif sort == 'most_viewed':
        query = query.order_by(Project.views_count.desc())
    else:  # newest by default
        query = query.order_by(Project.created_at.desc())

    return query
