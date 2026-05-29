# AI Resume Analyzer

A portfolio-friendly AI Resume Analyzer built with HTML, CSS, JavaScript, Flask, and the Groq API. It accepts PDF or DOCX resumes, extracts text, scores ATS readiness, checks missing resume sections, compares the resume with a target role, and generates practical feedback for students applying to internships or entry-level jobs.

## Features

- Upload PDF or DOCX resumes
- Automatic text extraction with `pypdf` and `python-docx`
- Groq-powered resume feedback when `GROQ_API_KEY` is configured
- Demo fallback analysis when no API key is available
- ATS score out of 100
- Missing section detection for Education, Skills, Projects, Experience, and Certifications
- Grammar, readability, action verb, and project description suggestions
- Role matching with match percentage, missing skills, and recommended technologies
- Skill gap analyzer with a short learning plan
- AI-style project suggestions
- Summary feedback and rewritten summary sample
- Dark/light mode toggle
- Chart.js dashboard charts
- Downloadable plain-text analysis report

## Folder Structure

```text
ai-resume-analyzer/
|-- app.py
|-- requirements.txt
|-- .env.example
|-- README.md
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- routes.py
|   |-- services/
|   |   |-- resume_analyzer.py
|   |   `-- report_service.py
|   |-- utils/
|   |   `-- text_extractor.py
|   |-- templates/
|   |   `-- index.html
|   `-- static/
|       |-- css/
|       |   `-- styles.css
|       `-- js/
|           `-- app.js
|-- sample_resumes/
|   |-- sample_resume.txt
|   `-- sample_resume.docx
`-- scripts/
    `-- create_sample_resume.py
```

## Setup Guide

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create your environment file:

```bash
copy .env.example .env
```

4. Add your Groq API key in `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
SECRET_KEY=replace-this-with-a-random-secret
```

5. Run the app:

```bash
python app.py
```

6. Open the local URL shown in the terminal, usually:

```text
http://127.0.0.1:5000
```

## Testing

Use `sample_resumes/sample_resume.docx` to test the DOCX parser. You can also export that file as PDF from Word or Google Docs to test the PDF flow.

The app still works without a Groq API key by using a local heuristic analysis. Add a real key when you want Groq-generated feedback.

## API Routes

- `GET /` renders the web app
- `GET /api/health` returns a basic health status
- `POST /api/analyze` accepts `resume` and optional `role` form data
- `POST /api/download-report` downloads the latest analysis as a text report

## Notes for Portfolio Use

- Keep the demo fallback enabled so reviewers can try the app without needing your API key.
- Add screenshots or a short walkthrough video to your portfolio page.
- If deploying, set `GROQ_API_KEY`, `GROQ_MODEL`, and `SECRET_KEY` as server environment variables.
