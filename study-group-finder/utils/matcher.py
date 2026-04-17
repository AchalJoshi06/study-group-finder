import re
from datetime import datetime

from utils.validators import split_csv_field


DEFAULT_WEIGHTS = {
    "subject_exact": 6.0,
    "subject_keyword_overlap": 2.5,
    "availability_overlap": 2.0,
    "open_seat_bonus": 1.5,
    "recent_group_bonus": 1.5,
}


def _tokenize(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def suggest_groups_for_user(user, groups, joined_group_ids, limit=5, weights=None):
    """Weighted recommendation scoring by subject fit, schedule overlap, seats, and recency."""
    active_weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    user_subjects = {s.lower() for s in split_csv_field(user.subjects)}
    user_subject_tokens = _tokenize(" ".join(user_subjects))

    user_availability_slots = {a.lower() for a in split_csv_field(user.availability)}
    user_availability_tokens = _tokenize(" ".join(user_availability_slots))

    scored_groups = []
    for group in groups:
        if group.id in joined_group_ids:
            continue

        if group.is_private:
            continue

        if group.current_member_count >= group.max_members:
            continue

        score = 0.0
        subject = (group.subject or "").lower()
        subject_tokens = _tokenize(subject)
        schedule = (group.schedule or "").lower()
        schedule_tokens = _tokenize(schedule)

        if subject in user_subjects:
            score += active_weights["subject_exact"]

        keyword_overlap = len(subject_tokens & user_subject_tokens)
        if keyword_overlap:
            score += min(keyword_overlap, 3) * active_weights["subject_keyword_overlap"]

        slot_overlap = len(schedule_tokens & user_availability_tokens)
        if slot_overlap:
            score += min(slot_overlap, 4) * active_weights["availability_overlap"]

        seats_left = group.max_members - group.current_member_count
        seat_ratio = seats_left / max(group.max_members, 1)
        score += seat_ratio * active_weights["open_seat_bonus"]

        age_days = max((datetime.utcnow() - group.created_at).days, 0)
        recency_bonus = max(0.0, 1 - (age_days / 14)) * active_weights["recent_group_bonus"]
        score += recency_bonus

        if score > 0:
            scored_groups.append((score, seats_left, group.created_at, group))

    scored_groups.sort(
        key=lambda item: (item[0], item[1], item[2]),
        reverse=True,
    )
    return [group for _, _, _, group in scored_groups[:limit]]
