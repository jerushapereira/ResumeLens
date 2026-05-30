import json
import re
from collections import Counter

import requests


SECTION_KEYWORDS = {
    "Education": ["education", "degree", "university", "college", "b.tech", "bachelor", "cgpa", "gpa"],
    "Skills": ["skills", "technical skills", "programming", "tools", "technologies"],
    "Projects": ["projects", "project", "portfolio", "github"],
    "Experience": ["experience", "internship", "work history", "employment", "volunteer"],
    "Certifications": ["certifications", "certificate", "certified", "course", "coursera", "udemy"],
}

ACTION_VERBS = {
    "built", "created", "designed", "developed", "implemented", "optimized", "improved", "deployed",
    "automated", "analyzed", "led", "managed", "collaborated", "tested", "integrated", "launched",
}

COMMON_SKILLS = {
    "python", "java", "javascript", "typescript", "html", "css", "react", "node", "flask", "django",
    "sql", "mysql", "postgresql", "mongodb", "git", "github", "docker", "aws", "azure", "linux",
    "excel", "power bi", "tableau", "machine learning", "data analysis", "pandas", "numpy", "api",
    "rest", "tailwind", "bootstrap", "figma", "firebase", "cloud", "nlp", "communication",
}

ROLE_SKILLS = {
    "frontend": ["HTML", "CSS", "JavaScript", "React", "Responsive Design", "Git", "Accessibility"],
    "backend": ["Python", "Flask", "REST APIs", "SQL", "Authentication", "Docker", "Testing"],
    "full stack": ["HTML", "CSS", "JavaScript", "React", "Python", "Flask", "SQL", "REST APIs", "Git"],
    "data analyst": ["Excel", "SQL", "Python", "Pandas", "Power BI", "Tableau", "Statistics"],
    "data scientist": ["Python", "Pandas", "NumPy", "Machine Learning", "Statistics", "SQL", "Model Evaluation"],
    "machine learning": ["Python", "Machine Learning", "NLP", "Scikit-learn", "Pandas", "Model Deployment"],
    "devops": ["Linux", "Docker", "CI/CD", "AWS", "Monitoring", "Scripting", "Git"],
    "ui ux": ["Figma", "Wireframing", "User Research", "Prototyping", "Design Systems", "Accessibility"],
}


class ResumeAnalyzer:
    def __init__(self, api_key="", model="llama-3.3-70b-versatile", api_url=""):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url

    def analyze(self, resume_text, desired_role):
        fallback = self._heuristic_analysis(resume_text, desired_role)

        if not self.api_key:
            fallback["ai_mode"] = "demo"
            fallback["notice"] = "No GROQ_API_KEY found. Heuristic demo analysis was used."
            return fallback

        try:
            ai_result = self._call_groq(resume_text, desired_role, fallback)
            merged = self._merge_with_defaults(ai_result, fallback)
            merged["ai_mode"] = "groq"
            return merged
        except Exception:
            fallback["ai_mode"] = "fallback"
            fallback["notice"] = "Groq analysis failed, so a local heuristic analysis was used."
            return fallback

    def _call_groq(self, resume_text, desired_role, fallback):
        prompt = self._build_prompt(resume_text, desired_role, fallback)
        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an ATS resume reviewer. Return only valid JSON with no markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.25,
                "max_tokens": 2200,
                "response_format": {"type": "json_object"},
            },
            timeout=35,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_json(content)

    def _build_prompt(self, resume_text, desired_role, fallback):
        return f"""
Analyze this student resume for ATS quality and internship readiness.

Desired role: {desired_role or "General internship / entry-level role"}

Return JSON using exactly these top-level keys:
ats_score, missing_sections, section_presence, suggestions, role_match, skill_gap,
summary_feedback, project_suggestions, quick_wins.

Rules:
- ats_score must be an integer from 0 to 100.
- section_presence values must be booleans for Education, Skills, Projects, Experience, Certifications.
- suggestions must include grammar, readability, action_verbs, project_descriptions arrays.
- role_match must include match_percentage, explanation, missing_skills, recommended_technologies.
- skill_gap must include present_skills, missing_skills, learning_plan.
- summary_feedback must include strengths, weaknesses, rewrite.
- project_suggestions and quick_wins must be arrays.
- Be practical, specific, and encouraging for a student portfolio.

Local heuristic starting point, improve it if needed:
{json.dumps(fallback)}

Resume text:
{resume_text[:9000]}
"""

    def _parse_json(self, content):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))

    def _merge_with_defaults(self, ai_result, fallback):
        if not isinstance(ai_result, dict):
            return fallback

        merged = {**fallback, **ai_result}
        merged["section_presence"] = {
            **fallback.get("section_presence", {}),
            **(ai_result.get("section_presence") or {}),
        }
        merged["suggestions"] = {
            **fallback.get("suggestions", {}),
            **(ai_result.get("suggestions") or {}),
        }
        merged["role_match"] = {
            **fallback.get("role_match", {}),
            **(ai_result.get("role_match") or {}),
        }
        merged["skill_gap"] = {
            **fallback.get("skill_gap", {}),
            **(ai_result.get("skill_gap") or {}),
        }
        merged["summary_feedback"] = {
            **fallback.get("summary_feedback", {}),
            **(ai_result.get("summary_feedback") or {}),
        }
        merged["ats_score"] = max(0, min(100, int(merged.get("ats_score", fallback["ats_score"]))))
        merged["role_match"]["match_percentage"] = max(
            0,
            min(100, int(merged["role_match"].get("match_percentage", fallback["role_match"]["match_percentage"]))),
        )
        return merged

    def _heuristic_analysis(self, resume_text, desired_role):
        lower_text = resume_text.lower()
        words = re.findall(r"[a-zA-Z+#.]+", lower_text)
        word_count = len(words)
        word_counter = Counter(words)

        section_presence = {
            section: any(keyword in lower_text for keyword in keywords)
            for section, keywords in SECTION_KEYWORDS.items()
        }
        missing_sections = [section for section, present in section_presence.items() if not present]

        present_skills = sorted({
            skill.title() if len(skill) > 3 else skill.upper()
            for skill in COMMON_SKILLS
            if skill in lower_text
        })

        target_skills = self._skills_for_role(desired_role)
        normalized_present = {skill.lower() for skill in present_skills}
        missing_role_skills = [
            skill for skill in target_skills
            if skill.lower() not in normalized_present and skill.lower() not in lower_text
        ]

        section_score = sum(section_presence.values()) * 10
        length_score = 18 if 350 <= word_count <= 900 else 12 if word_count >= 200 else 6
        action_score = min(16, sum(1 for verb in ACTION_VERBS if verb in lower_text) * 2)
        metric_score = 12 if re.search(r"\d+%|\d+\+|\$\d+|\b\d{2,}\b", resume_text) else 4
        role_score = 14 if target_skills else 10
        if target_skills:
            role_score = round((len(target_skills) - len(missing_role_skills)) / len(target_skills) * 14)

        ats_score = max(30, min(96, section_score + length_score + action_score + metric_score + role_score))
        match_percentage = 55 if not target_skills else max(
            25,
            min(95, round((len(target_skills) - len(missing_role_skills)) / len(target_skills) * 100)),
        )

        repeated_soft_words = [
            word for word, count in word_counter.items()
            if count >= 5 and word in {"responsible", "worked", "helped", "made", "good"}
        ]

        return {
            "ats_score": ats_score,
            "missing_sections": missing_sections,
            "section_presence": section_presence,
            "suggestions": {
                "grammar": [
                    "Use consistent tense: present tense for current roles and past tense for completed projects.",
                    "Keep bullets short and avoid first-person wording like 'I' or 'my'.",
                ],
                "readability": [
                    "Use 3-5 bullets per major project or experience so recruiters can scan quickly.",
                    "Start each bullet with the result, then mention the tool or method used.",
                ],
                "action_verbs": [
                    "Replace weak verbs with stronger ones such as built, automated, optimized, designed, or deployed.",
                    f"Review repeated weak wording: {', '.join(repeated_soft_words)}." if repeated_soft_words else "Add more action verbs to the first word of each bullet.",
                ],
                "project_descriptions": [
                    "For each project, include problem, tech stack, your contribution, and measurable outcome.",
                    "Add links to GitHub, live demos, or screenshots when available.",
                ],
            },
            "role_match": {
                "match_percentage": match_percentage,
                "explanation": "Match is estimated from detected skills, project evidence, and target role keywords.",
                "missing_skills": missing_role_skills[:8],
                "recommended_technologies": missing_role_skills[:5] or target_skills[:5],
            },
            "skill_gap": {
                "present_skills": present_skills[:18],
                "missing_skills": missing_role_skills[:10],
                "learning_plan": self._learning_plan(missing_role_skills),
            },
            "summary_feedback": {
                "strengths": self._strength_summary(section_presence, present_skills),
                "weaknesses": self._weakness_summary(missing_sections, missing_role_skills),
                "rewrite": self._summary_rewrite(desired_role, present_skills),
            },
            "project_suggestions": self._project_suggestions(desired_role, missing_role_skills),
            "quick_wins": [
                "Add a one-line professional summary under your name.",
                "Quantify at least three bullets with numbers, percentages, users, time saved, or accuracy.",
                "Move the strongest role-relevant projects above less relevant details.",
                "Include clean links for GitHub, LinkedIn, portfolio, and email.",
            ],
        }

    def _skills_for_role(self, desired_role):
        role = (desired_role or "").lower()
        for keyword, skills in ROLE_SKILLS.items():
            if keyword in role:
                return skills
        if "software" in role or "developer" in role:
            return ROLE_SKILLS["full stack"]
        return ["Communication", "Git", "Problem Solving", "Projects", "SQL", "Python"]

    def _learning_plan(self, missing_skills):
        if not missing_skills:
            return ["Build one polished project that combines your strongest skills and deploy it publicly."]

        return [
            f"Spend 3-4 days learning the basics of {skill}, then use it in a small project."
            for skill in missing_skills[:4]
        ] + ["Update the resume with proof: project link, metric, and short bullet about the result."]

    def _strength_summary(self, section_presence, present_skills):
        present_sections = [section for section, present in section_presence.items() if present]
        skills = ", ".join(present_skills[:5]) if present_skills else "your technical foundation"
        return f"The resume already shows {', '.join(present_sections) or 'core resume content'} and highlights {skills}."

    def _weakness_summary(self, missing_sections, missing_role_skills):
        issues = []
        if missing_sections:
            issues.append("missing sections: " + ", ".join(missing_sections))
        if missing_role_skills:
            issues.append("role skill gaps: " + ", ".join(missing_role_skills[:5]))
        return "; ".join(issues) if issues else "No major structural weakness detected; focus on stronger metrics and clarity."

    def _summary_rewrite(self, desired_role, present_skills):
        role = desired_role or "entry-level technology role"
        skills = ", ".join(present_skills[:4]) if present_skills else "programming, teamwork, and project building"
        return (
            f"Motivated student targeting a {role}, with hands-on experience in {skills}. "
            "Interested in building practical, user-focused solutions and improving through real project work."
        )

    def _project_suggestions(self, desired_role, missing_skills):
        role = (desired_role or "").lower()
        if "data" in role:
            return [
                "Build a student placement dashboard using Python, SQL, and Power BI/Tableau.",
                "Create an end-to-end notebook that cleans messy data, visualizes trends, and explains insights.",
                "Deploy a simple prediction app with Flask and a documented model evaluation section.",
            ]
        if "frontend" in role or "ui" in role:
            return [
                "Create a responsive internship tracker with filters, saved jobs, and local storage.",
                "Build a portfolio case-study page with before/after UI improvements and accessibility notes.",
                "Recreate a dashboard from a real product and document component decisions.",
            ]
        if "backend" in role or "api" in role:
            return [
                "Build a Flask REST API with authentication, pagination, validation, and tests.",
                "Create a mini task manager API with PostgreSQL and Docker setup instructions.",
                "Add API documentation using Swagger/OpenAPI and include request examples.",
            ]
        return [
            "Build a role-focused capstone project with login, dashboard, database, and deployment.",
            "Create a real-world automation tool that saves time and shows before/after results.",
            "Add one AI-powered feature to an existing project and document the prompt and limitations.",
        ]
