"""Enum domain. Sumber kebenaran tunggal untuk Node 0 (Input Sanitizer)."""

from enum import StrEnum


class CareerTrack(StrEnum):
    """Satu-satunya nilai target_career yang boleh masuk ke LLM."""

    BACKEND_DEVELOPER = "Backend Developer"
    DATA_SCIENTIST = "Data Scientist"
    DEVOPS_ENGINEER = "DevOps Engineer"
