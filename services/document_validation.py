"""Validate uploaded CV and certificates match application form data."""
from __future__ import annotations

import re
from pathlib import Path

from services.cv_scoring import extract_resume_text, normalize_text

EDUCATION_HINTS = {
    "high school": ["high school", "secondary", "matric", "o level", "a level"],
    "diploma": ["diploma", "certificate", "national diploma", "hnd"],
    "bachelor's degree": ["bachelor", "bsc", "ba", "undergraduate", "degree"],
    "master's degree": ["master", "msc", "ma", "mba", "postgraduate"],
    "phd": ["phd", "doctorate", "doctoral", "dphil"],
}


def _digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _text_contains_name(text: str, name: str, surname: str) -> bool:
    normalized = normalize_text(text)
    first = normalize_text(name)
    surname_norm = normalize_text(surname)
    if first and first in normalized:
        return True
    if surname_norm and surname_norm in normalized:
        return True
    if first and surname_norm:
        full = f"{first} {surname_norm}".strip()
        if full and full in normalized:
            return True
    return False


def _education_hints(education: str) -> list[str]:
    key = normalize_text(education)
    for label, hints in EDUCATION_HINTS.items():
        if label in key or key in label:
            return hints
    return [key] if key else []


def _education_mentioned(text: str, education: str) -> bool:
    hints = _education_hints(education)
    normalized = normalize_text(text)
    return any(hint in normalized for hint in hints if hint)


def _read_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".pdf", ".docx", ".txt"}:
        return extract_resume_text(path)
    return path.stem


def validate_application_documents(
    name: str,
    surname: str,
    email: str,
    phone: str,
    education: str,
    resume_path: Path,
    cert_paths: list[Path],
) -> list[str]:
    errors: list[str] = []

    try:
        cv_text = extract_resume_text(resume_path)
    except Exception:
        return ["Could not read the uploaded CV. Please upload a valid PDF, DOCX, or TXT file."]

    if not _text_contains_name(cv_text, name, surname):
        errors.append("Your CV does not appear to contain the name you entered.")

    if email and normalize_text(email) not in normalize_text(cv_text):
        errors.append("Your CV does not contain the email address you entered.")

    phone_digits = _digits_only(phone)
    cv_digits = _digits_only(cv_text)
    if phone_digits and phone_digits[-8:] not in cv_digits:
        errors.append("Your CV does not contain the phone number you entered.")

    if education and not _education_mentioned(cv_text, education):
        errors.append("Your CV does not mention the education level you selected.")

    for cert_path in cert_paths:
        label = cert_path.name
        try:
            cert_text = _read_document_text(cert_path)
        except Exception:
            cert_text = cert_path.stem

        combined = f"{cert_text} {cert_path.name}"
        if not _text_contains_name(combined, name, surname):
            errors.append(f"Certificate '{label}' does not appear to match your name.")

        if education and cert_path.suffix.lower() in {".pdf", ".docx", ".txt"}:
            if not _education_mentioned(combined, education):
                errors.append(
                    f"Certificate '{label}' does not appear to relate to your education ({education})."
                )

    return errors
