"""Guard otomatis aturan modul sertifikasi (Free First, No Price, No Raw URL)."""

import json
import re
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.schemas.enums import CareerTrack

KB_FILE = Path(get_settings().knowledge_base_dir) / "certifications.json"
ALLOWED_KEYS = {
    "id",
    "provider",
    "title",
    "level",
    "skills",
    "prerequisite_skills",
    "search_query",
}
FREE_PROVIDERS = {
    "FreeCodeCamp",
    "Kaggle",
    "Cisco Networking Academy",
    "Google Cloud Skills Boost",
    "Microsoft Applied Skills",
}
PAID_PROVIDERS = {"AWS", "Oracle", "CNCF / Linux Foundation", "CompTIA"}
FORBIDDEN_TEXT = re.compile(r"https?://|www\.|\$\s?\d|\bUSD\b|\bIDR\b|\bRp\.?\s?\d", re.IGNORECASE)


@pytest.fixture(scope="module")
def kb() -> dict:
    if not KB_FILE.exists():
        pytest.skip(f"{KB_FILE} tidak ditemukan (knowledge_base tidak ter-mount)")
    return json.loads(KB_FILE.read_text(encoding="utf-8"))


def test_roles_match_career_enum(kb: dict) -> None:
    assert set(kb["roles"]) == {c.value for c in CareerTrack}


def test_free_options_come_first(kb: dict) -> None:
    for role, data in kb["roles"].items():
        assert list(data.keys()) == ["free_options", "paid_options"], role
        assert data["free_options"], f"{role}: free_options kosong"


def test_provider_split(kb: dict) -> None:
    for role, data in kb["roles"].items():
        assert {o["provider"] for o in data["free_options"]} <= FREE_PROVIDERS, role
        assert {o["provider"] for o in data["paid_options"]} <= PAID_PROVIDERS, role


def test_entry_schema_and_unique_ids(kb: dict) -> None:
    seen: set[str] = set()
    for role, data in kb["roles"].items():
        for opt in data["free_options"] + data["paid_options"]:
            assert set(opt) == ALLOWED_KEYS, f"{role}/{opt.get('id')}"
            assert opt["id"] not in seen, f"id duplikat: {opt['id']}"
            seen.add(opt["id"])
            assert opt["search_query"].strip(), opt["id"]


def test_no_price_and_no_raw_url(kb: dict) -> None:
    blob = json.dumps(kb["roles"], ensure_ascii=False)
    assert not FORBIDDEN_TEXT.search(blob)
    assert '"price"' not in blob and '"url"' not in blob
