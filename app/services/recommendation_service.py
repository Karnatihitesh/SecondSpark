import re
from app.models.user import User
from app.models.project import Project

def _tokenize(text):
    """Normalize and tokenize text into words for matching."""
    if not text:
        return set()
    words = re.findall(r'[a-zA-Z0-9+#]+', text.lower())
    stop_words = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'with', 'for', 'to', 'of', 'at', 'by', 'is', 'it'}
    return set(w for w in words if w not in stop_words and len(w) > 1)


def recommend_repairmen_for_project(project, limit=4):
    """
    Ranks and recommends the best matching repairmen/contributors for a given project.
    
    Ranking factors:
    1. Rating Quality (35%) - Bayesian damped average
    2. Skill/Tech Match (30%) - Jaccard overlap + keyword containment
    3. Completed Projects History (15%) - Number of completed repairs
    4. Category Experience (10%) - Completed builds in this category
    5. Availability / Workload (5%) - Current active workload capacity
    6. Review Count / Reliability (5%) - Statistical confidence in feedback
    """
    if not project:
        return {'recommendations': [], 'is_fallback': False}

    proj_skills = set(s.strip().lower() for s in project.skills_list)
    proj_text_tokens = _tokenize(f"{project.title} {project.required_skills} {project.short_summary} {project.problems_faults} {project.help_required}")

    candidates = User.query.filter(
        User.id != project.user_id,
        User.is_active == True,
        User.role != 'admin'
    ).all()

    if not candidates:
        candidates = User.query.filter(
            User.id != project.user_id,
            User.is_active == True
        ).all()

    if not candidates:
        return {'recommendations': [], 'is_fallback': False}

    scored_candidates = []
    has_any_skill_match = False

    R_PRIOR = 4.0
    M_WEIGHT = 2.0

    for user in candidates:
        # 1. Rating Quality (35%)
        rev_count = user.reviews_count
        avg_rating = user.average_rating if rev_count > 0 else R_PRIOR
        bayesian_rating = ((rev_count * avg_rating) + (M_WEIGHT * R_PRIOR)) / (rev_count + M_WEIGHT)
        rating_score = max(0.0, min(1.0, (bayesian_rating - 1.0) / 4.0))

        # 2. Skill & Tech Match (30%)
        user_skills = set(s.strip().lower() for s in user.skills_list)
        user_text_tokens = _tokenize(f"{user.skills} {user.bio}")
        
        direct_matches = proj_skills.intersection(user_skills)
        token_matches = proj_text_tokens.intersection(user_text_tokens)
        
        skill_score = 0.0
        reasons = []

        if proj_skills:
            skill_jaccard = len(direct_matches) / len(proj_skills)
            token_overlap = min(1.0, len(token_matches) / max(3, len(proj_skills)))
            skill_score = (0.7 * skill_jaccard) + (0.3 * token_overlap)
        elif proj_text_tokens:
            skill_score = min(1.0, len(token_matches) / 5.0)

        if direct_matches:
            has_any_skill_match = True
            matched_str = ', '.join(sorted(direct_matches)[:3])
            reasons.append(f"Strong match in {matched_str}")
        elif token_matches:
            has_any_skill_match = True
            matched_str = ', '.join(sorted(token_matches)[:2])
            reasons.append(f"Familiar with {matched_str}")

        # 3. Completed Projects History (15%)
        completed_repairs = user.projects_repaired_count
        history_score = min(1.0, completed_repairs / 15.0)
        if completed_repairs > 0:
            reasons.append(f"Repaired {completed_repairs} completed builds")

        # 4. Category Experience (10%)
        category_repairs = user.assigned_projects.filter(
            Project.category_id == project.category_id,
            Project.status == 'Completed'
        ).count()
        category_score = min(1.0, category_repairs / 3.0)
        if category_repairs > 0 and project.category:
            reasons.append(f"Completed {category_repairs} {project.category.name} builds")

        # 5. Availability & Workload (5%)
        active_work = user.active_repairs_count
        if active_work == 0:
            avail_score = 1.0
            reasons.append("Immediate availability")
        elif active_work <= 2:
            avail_score = 0.8
        elif active_work <= 4:
            avail_score = 0.5
        else:
            avail_score = 0.2

        # 6. Review Count (5%)
        reliability_score = min(1.0, rev_count / 10.0)
        if rev_count >= 5 and avg_rating >= 4.5:
            reasons.append(f"Top rated maker ({avg_rating}★ across {rev_count} reviews)")

        composite = (
            (0.35 * rating_score) +
            (0.30 * skill_score) +
            (0.15 * history_score) +
            (0.10 * category_score) +
            (0.05 * avail_score) +
            (0.05 * reliability_score)
        )

        match_pct = int(round(60 + (composite * 38)))
        match_pct = max(60, min(98, match_pct))

        badge = "Recommended"
        if skill_score > 0.6 and match_pct >= 90:
            badge = "Top Match"
        elif completed_repairs >= 5:
            badge = "Veteran Maker"
        elif avg_rating >= 4.8 and rev_count >= 3:
            badge = "High Rating"
        elif active_work == 0:
            badge = "Available Now"

        if not reasons:
            reasons.append("Experienced community contributor ready to collaborate")

        scored_candidates.append({
            'repairman': user,
            'match_score': match_pct,
            'badge': badge,
            'match_reasons': reasons[:3],
            'direct_matches': list(direct_matches),
            'projects_repaired': completed_repairs,
            'active_repairs': active_work,
            'rating': user.average_rating,
            'reviews_count': rev_count,
            'composite': composite
        })

    scored_candidates.sort(key=lambda x: x['composite'], reverse=True)
    is_fallback = not has_any_skill_match
    return {
        'recommendations': scored_candidates[:limit],
        'is_fallback': is_fallback
    }
