const form = document.getElementById("analyzeForm");
const fileInput = document.getElementById("resumeFile");
const fileName = document.getElementById("fileName");
const dropZone = document.getElementById("dropZone");
const roleInput = document.getElementById("roleInput");
const analyzeButton = document.getElementById("analyzeButton");
const formError = document.getElementById("formError");
const apiStatus = document.getElementById("apiStatus");
const results = document.getElementById("results");
const themeToggle = document.getElementById("themeToggle");
const downloadReport = document.getElementById("downloadReport");

let latestPayload = null;
let matchChart = null;
let sectionsChart = null;

const sectionNames = ["Education", "Skills", "Projects", "Experience", "Certifications"];

function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("resumeLensTheme", theme);
}

function getSavedTheme() {
    return localStorage.getItem("resumeLensTheme") || "light";
}

function setLoading(isLoading) {
    analyzeButton.disabled = isLoading;
    analyzeButton.textContent = isLoading ? "Analyzing..." : "Analyze Resume";
    apiStatus.textContent = isLoading ? "Working" : "Ready";
}

function showError(message) {
    formError.textContent = message || "";
    if (message) {
        apiStatus.textContent = "Needs fix";
    }
}

function escapeText(value) {
    return String(value || "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#039;",
    }[char]));
}

function listItems(items) {
    if (!Array.isArray(items) || items.length === 0) {
        return "<p>No items found.</p>";
    }
    return `<ul>${items.map((item) => `<li>${escapeText(item)}</li>`).join("")}</ul>`;
}

function textBlock(title, content) {
    const body = Array.isArray(content) ? listItems(content) : `<p>${escapeText(content || "No feedback available.")}</p>`;
    return `<div class="text-block"><strong>${escapeText(title)}</strong>${body}</div>`;
}

function updateScore(score) {
    const cleanScore = Math.max(0, Math.min(100, Number(score) || 0));
    const ring = document.getElementById("atsRing");
    document.getElementById("atsScore").textContent = cleanScore;
    ring.style.setProperty("--score", cleanScore);

    const note = cleanScore >= 80
        ? "Strong resume. Focus on role-specific polish."
        : cleanScore >= 60
            ? "Good foundation. A few targeted edits can raise this quickly."
            : "Needs structure, clearer sections, and stronger project evidence.";
    document.getElementById("scoreNote").textContent = note;
}

function renderCharts(analysis) {
    if (!window.Chart) {
        return;
    }

    const chartTextColor = getComputedStyle(document.documentElement).getPropertyValue("--text").trim();
    const matchPercentage = Number(analysis.role_match?.match_percentage) || 0;
    const presentSections = sectionNames.map((section) => analysis.section_presence?.[section] ? 1 : 0);

    if (matchChart) {
        matchChart.destroy();
    }
    if (sectionsChart) {
        sectionsChart.destroy();
    }

    matchChart = new Chart(document.getElementById("matchChart"), {
        type: "doughnut",
        data: {
            labels: ["Match", "Gap"],
            datasets: [{
                data: [matchPercentage, 100 - matchPercentage],
                backgroundColor: ["#E0C58F", "rgba(60, 80, 125, 0.18)"],
                borderWidth: 0,
            }],
        },
        options: {
            plugins: {
                legend: { position: "bottom", labels: { color: chartTextColor } },
                tooltip: { callbacks: { label: (item) => `${item.label}: ${item.raw}%` } },
            },
            cutout: "68%",
        },
    });

    sectionsChart = new Chart(document.getElementById("sectionsChart"), {
        type: "bar",
        data: {
            labels: sectionNames,
            datasets: [{
                label: "Present",
                data: presentSections,
                backgroundColor: ["#3C507D", "#E0C58F", "#112250", "#D9CBC2", "#7890BF"],
                borderRadius: 6,
            }],
        },
        options: {
            scales: {
                x: { ticks: { color: chartTextColor }, grid: { display: false } },
                y: {
                    min: 0,
                    max: 1,
                    ticks: {
                        color: chartTextColor,
                        callback: (value) => value === 1 ? "Yes" : "No",
                    },
                    grid: { color: "rgba(120, 144, 191, 0.16)" },
                },
            },
            plugins: {
                legend: { display: false },
            },
        },
    });
}

function renderSections(analysis) {
    const badges = document.getElementById("sectionBadges");
    const missing = analysis.missing_sections || [];
    document.getElementById("missingCount").textContent = `${missing.length} found`;

    badges.innerHTML = sectionNames.map((section) => {
        const present = Boolean(analysis.section_presence?.[section]);
        return `<span class="badge ${present ? "is-present" : "is-missing"}">${escapeText(section)}: ${present ? "Present" : "Missing"}</span>`;
    }).join("");
}

function renderSummary(analysis) {
    const summary = analysis.summary_feedback || {};
    document.getElementById("summaryFeedback").innerHTML = [
        textBlock("Strengths", summary.strengths),
        textBlock("Weaknesses", summary.weaknesses),
        textBlock("Suggested Summary", summary.rewrite),
    ].join("");
}

function renderSuggestions(analysis) {
    const suggestions = analysis.suggestions || {};
    const labels = {
        grammar: "Grammar",
        readability: "Readability",
        action_verbs: "Action Verbs",
        project_descriptions: "Projects",
    };

    document.getElementById("suggestionsGrid").innerHTML = Object.entries(labels).map(([key, label]) => `
        <div class="suggestion-card">
            <h4>${label}</h4>
            ${listItems(suggestions[key])}
        </div>
    `).join("");
}

function renderSkillGap(analysis) {
    const skillGap = analysis.skill_gap || {};
    document.getElementById("skillGap").innerHTML = [
        textBlock("Detected Skills", skillGap.present_skills),
        textBlock("Missing Skills", skillGap.missing_skills),
        textBlock("Learning Plan", skillGap.learning_plan),
    ].join("");
}

function renderRoleMatch(analysis) {
    const roleMatch = analysis.role_match || {};
    document.getElementById("roleMatch").innerHTML = [
        textBlock("Match", `${roleMatch.match_percentage || 0}% - ${roleMatch.explanation || ""}`),
        textBlock("Missing Skills", roleMatch.missing_skills),
        textBlock("Recommended Technologies", roleMatch.recommended_technologies),
    ].join("");
}

function renderProjects(analysis) {
    const projects = analysis.project_suggestions || [];
    document.getElementById("projectSuggestions").innerHTML = projects.length
        ? projects.map((project) => `<div class="project-item">${escapeText(project)}</div>`).join("")
        : "<p>No project suggestions returned.</p>";
}

function renderResults(payload) {
    const analysis = payload.analysis;
    latestPayload = payload;
    document.getElementById("resultTitle").textContent = `${payload.filename} report`;

    updateScore(analysis.ats_score);
    renderSections(analysis);
    renderSummary(analysis);
    renderSuggestions(analysis);
    renderSkillGap(analysis);
    renderRoleMatch(analysis);
    renderProjects(analysis);
    renderCharts(analysis);

    results.classList.remove("hidden");
    apiStatus.textContent = analysis.ai_mode === "groq" ? "Groq AI" : "Demo mode";
    results.scrollIntoView({ behavior: "smooth", block: "start" });
}

fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];
    fileName.textContent = file ? file.name : "No file selected";
    showError("");
});

["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("drag-over");
    });
});

["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("drag-over");
    });
});

dropZone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0];
    if (!file) {
        return;
    }
    fileInput.files = event.dataTransfer.files;
    fileName.textContent = file.name;
    showError("");
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    showError("");

    const file = fileInput.files[0];
    if (!file) {
        showError("Please choose a PDF or DOCX resume first.");
        return;
    }

    const extension = file.name.split(".").pop().toLowerCase();
    if (!["pdf", "docx"].includes(extension)) {
        showError("Only PDF and DOCX files are supported.");
        return;
    }

    const formData = new FormData();
    formData.append("resume", file);
    formData.append("role", roleInput.value.trim());

    try {
        setLoading(true);
        const response = await fetch("/api/analyze", {
            method: "POST",
            body: formData,
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Analysis failed.");
        }

        renderResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
});

downloadReport.addEventListener("click", async () => {
    if (!latestPayload) {
        showError("Analyze a resume before downloading a report.");
        return;
    }

    try {
        const response = await fetch("/api/download-report", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(latestPayload),
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Could not download report.");
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${latestPayload.filename}-analysis-report.txt`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    } catch (error) {
        showError(error.message);
    }
});

themeToggle.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    if (latestPayload) {
        renderCharts(latestPayload.analysis);
    }
});

setTheme(getSavedTheme());
