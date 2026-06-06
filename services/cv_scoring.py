from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from docx import Document
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SKILL_KEYWORDS = [
    "python",
    "flask",
    "django",
    "fastapi",
    "java",
    "javascript",
    "typescript",
    "react",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "machine learning",
    "ai",
    "nlp",
    "data analysis",
    "pandas",
    "numpy",
    "excel",
    "power bi",
    "tableau",
    "aws",
    "azure",
    "docker",
    "kubernetes",
    "git",
    "leadership",
    "communication",
    "project management",
    "hr",
    "recruitment",
]

EDUCATION_LEVELS = {
    "phd": 4,
    "doctor": 4,
    "master": 3,
    "mba": 3,
    "bachelor": 2,
    "undergraduate": 2,
    "associate": 1,
    "diploma": 1,
}


@dataclass
class CandidateScore:
    name: str
    filename: str
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    summary: str
    recommendation: str
    recommendation_reason: str
    status: str


@dataclass(frozen=True)
class ResumeUpload:
    label: str
    path: Path


def rank_candidates(job_description: str, resume_paths: Iterable[ResumeUpload | Path]) -> list[CandidateScore]:
    resume_items = [normalize_resume_upload(item) for item in resume_paths]
    resume_texts = [extract_resume_text(item.path) for item in resume_items]
    documents = [job_description] + resume_texts

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(documents)
    job_vector = tfidf_matrix[0:1]

    required_years = extract_required_years(job_description)
    required_education = extract_required_education(job_description)
    job_skill_keywords = find_keywords(job_description)

    ranked_candidates: list[CandidateScore] = []
    for index, item in enumerate(resume_items, start=1):
        resume_text = resume_texts[index - 1]
        resume_vector = tfidf_matrix[index:index + 1]

        semantic_score = float(cosine_similarity(job_vector, resume_vector)[0][0])
        matched_skills = sorted(set(job_skill_keywords) & set(find_keywords(resume_text)))
        missing_skills = sorted(set(job_skill_keywords) - set(matched_skills))

        skill_score = len(matched_skills) / max(len(job_skill_keywords), 1)
        years_score = score_years(resume_text, required_years)
        education_score = score_education(resume_text, required_education)

        final_score = round(
            100
            * (
                0.50 * semantic_score
                + 0.30 * skill_score
                + 0.12 * years_score
                + 0.08 * education_score
            ),
            1,
        )

        summary = build_summary(
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            years_score=years_score,
            education_score=education_score,
            required_years=required_years,
            required_education=required_education,
        )

        recommendation, recommendation_reason = build_recommendation(final_score, matched_skills, missing_skills)
        status = determine_status(final_score, required_years, years_score)

        ranked_candidates.append(
            CandidateScore(
                name=item.label.replace("_", " ").title(),
                filename=item.path.name,
                score=final_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                summary=summary,
                recommendation=recommendation,
                recommendation_reason=recommendation_reason,
                status=status,
            )
        )

    ranked_candidates.sort(key=lambda item: item.score, reverse=True)
    return ranked_candidates


def normalize_resume_upload(item: ResumeUpload | Path) -> ResumeUpload:
    if isinstance(item, ResumeUpload):
        return item
    return ResumeUpload(label=item.stem, path=item)


def extract_resume_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix == ".docx":
        return extract_docx_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return normalize_text(" ".join(parts))


def extract_docx_text(path: Path) -> str:
    document = Document(str(path))
    return normalize_text(" ".join(paragraph.text for paragraph in document.paragraphs))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def find_keywords(text: str) -> list[str]:
    normalized_text = normalize_text(text)
    return [keyword for keyword in SKILL_KEYWORDS if keyword in normalized_text]


def extract_required_years(text: str) -> int | None:
    matches = re.findall(r"(\d{1,2})\+?\s+years?", normalize_text(text))
    if not matches:
        return None
    return max(int(match) for match in matches)


def score_years(text: str, required_years: int | None) -> float:
    candidate_years = extract_candidate_years(text)
    if required_years is None:
        return 0.5 if candidate_years is None else min(candidate_years / 10.0, 1.0)
    if candidate_years is None:
        return 0.0
    return min(candidate_years / required_years, 1.0)


def extract_candidate_years(text: str) -> int | None:
    matches = re.findall(r"(\d{1,2})\+?\s+years?", normalize_text(text))
    if not matches:
        return None
    return max(int(match) for match in matches)


def extract_required_education(text: str) -> int | None:
    normalized = normalize_text(text)
    for keyword, level in EDUCATION_LEVELS.items():
        if keyword in normalized:
            return level
    return None


def score_education(text: str, required_level: int | None) -> float:
    normalized = normalize_text(text)
    candidate_level = 0
    for keyword, level in EDUCATION_LEVELS.items():
        if keyword in normalized:
            candidate_level = max(candidate_level, level)
    if required_level is None:
        return 0.5 if candidate_level else 0.3
    if candidate_level == 0:
        return 0.0
    return min(candidate_level / required_level, 1.0)


def build_summary(
    *,
    matched_skills: list[str],
    missing_skills: list[str],
    years_score: float,
    education_score: float,
    required_years: int | None,
    required_education: int | None,
) -> str:
    parts = []
    if matched_skills:
        parts.append(f"Matched skills: {', '.join(matched_skills[:5])}.")
    if missing_skills:
        parts.append(f"Missing skills: {', '.join(missing_skills[:5])}.")
    if required_years is not None:
        parts.append(f"Experience alignment: {int(years_score * 100)}% against a {required_years}+ year requirement.")
    if required_education is not None:
        parts.append(f"Education alignment: {int(education_score * 100)}%.")
    if not parts:
        parts.append("The resume was scored against semantic similarity and keyword overlap.")
    return " ".join(parts)


def build_recommendation(score: float, matched_skills: list[str], missing_skills: list[str]) -> tuple[str, str]:
    if score >= 80:
        return "Strong hire", "High relevance to the role requirements and strong keyword overlap."
    if score >= 60:
        return "Interview", "Good fit, but worth validating experience depth in an interview."
    if matched_skills:
        return "Keep warm", "Some matching skills were found, but the profile is not yet a top fit."
    return "Reject", "The CV does not align closely with the job description."


def determine_status(score: float, required_years: int | None, years_score: float) -> str:
    if score >= 80:
        return "shortlisted"
    if required_years is not None and years_score < 0.75:
        return "pending review"
    if score >= 60:
        return "review"
    return "rejected"