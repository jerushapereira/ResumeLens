from datetime import datetime


def build_report(filename, desired_role, analysis):
    lines = [
        "AI RESUME ANALYZER REPORT",
        "=" * 32,
        f"Resume: {filename}",
        f"Target role: {desired_role}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"ATS Score: {analysis.get('ats_score', 0)}/100",
        f"Role Match: {analysis.get('role_match', {}).get('match_percentage', 0)}%",
        "",
        "Missing Sections",
        "-" * 16,
    ]

    missing_sections = analysis.get("missing_sections") or []
    lines.extend([f"- {item}" for item in missing_sections] or ["- None detected"])

    lines.extend(["", "Summary Feedback", "-" * 16])
    summary = analysis.get("summary_feedback", {})
    for key in ("strengths", "weaknesses", "rewrite"):
        value = summary.get(key)
        if value:
            lines.append(f"{key.title()}: {value}")

    lines.extend(["", "Improvement Suggestions", "-" * 23])
    suggestions = analysis.get("suggestions", {})
    for category, items in suggestions.items():
        lines.append(category.replace("_", " ").title() + ":")
        if isinstance(items, list):
            lines.extend([f"- {item}" for item in items])
        elif items:
            lines.append(f"- {items}")

    role_match = analysis.get("role_match", {})
    lines.extend(["", "Role Matching", "-" * 13])
    lines.append(f"Match explanation: {role_match.get('explanation', 'No explanation provided.')}")
    lines.append("Missing skills:")
    lines.extend([f"- {item}" for item in role_match.get("missing_skills", [])] or ["- None listed"])
    lines.append("Recommended technologies:")
    lines.extend([f"- {item}" for item in role_match.get("recommended_technologies", [])] or ["- None listed"])

    skill_gap = analysis.get("skill_gap", {})
    lines.extend(["", "Skill Gap Analyzer", "-" * 18])
    lines.append("Present skills:")
    lines.extend([f"- {item}" for item in skill_gap.get("present_skills", [])] or ["- None detected"])
    lines.append("Learning plan:")
    lines.extend([f"- {item}" for item in skill_gap.get("learning_plan", [])] or ["- No plan provided"])

    lines.extend(["", "AI Project Suggestions", "-" * 22])
    lines.extend([f"- {item}" for item in analysis.get("project_suggestions", [])] or ["- No suggestions provided"])

    lines.extend(["", "Quick Wins", "-" * 10])
    lines.extend([f"- {item}" for item in analysis.get("quick_wins", [])] or ["- No quick wins provided"])

    return "\n".join(lines)
