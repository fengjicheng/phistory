from __future__ import annotations

import hashlib
import json
import math
import re
from functools import lru_cache
from importlib import resources
from typing import Any

from phistory.static_prompts.models import CatalogEntry, CatalogSample, StaticPromptCandidate, StaticPromptMatch

_CATALOG_ROOT = "phistory.static_prompts.catalogs"
_WHITESPACE_RE = re.compile(r"[ \t]+")
_ALL_WHITESPACE_RE = re.compile(r"\s+")
_VERSION_RE = re.compile(r"\b\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?\b")
_BUILD_TIME_RE = re.compile(r'BUILD_TIME\s*:\s*"[^"]+"')
_HEX_RE = re.compile(r"\b[0-9a-f]{12,}\b", re.IGNORECASE)
_TEMPLATE_EXPR_RE = re.compile(r"\$\{[^{}\n]{0,240}\}")
_MARKDOWN_ESCAPE_RE = re.compile(r"\\([`*_{}\[\]()#+.!-])")


@lru_cache(maxsize=None)
def load_catalog(agent_id: str) -> tuple[CatalogEntry, ...]:
    try:
        catalog_path = resources.files(_CATALOG_ROOT).joinpath(agent_id, "known-prompts.json")
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ModuleNotFoundError):
        return ()
    entries: list[CatalogEntry] = []
    for raw in payload.get("entries", []):
        samples = tuple(_sample(item) for item in raw.get("samples", []) if isinstance(item, dict))
        raw_hashes = tuple(str(item) for item in raw.get("hashes", []) if item)
        sample_hashes = frozenset(
            (*raw_hashes, *(content_hash(sample.content) for sample in samples if sample.content))
        )
        anchors = tuple(str(anchor) for anchor in raw.get("anchors", []) if anchor)
        if not anchors:
            anchors = tuple(anchor for sample in samples for anchor in sample.anchors)
        entries.append(
            CatalogEntry(
                id=str(raw.get("id") or ""),
                name=str(raw.get("name") or raw.get("id") or ""),
                description=str(raw.get("description") or ""),
                category=str(raw.get("category") or "prompt"),
                samples=samples,
                anchors=anchors,
                sample_hashes=sample_hashes,
            )
        )
    return tuple(entry for entry in entries if entry.id and (entry.samples or entry.anchors or entry.sample_hashes))


def match_candidates(
    agent_id: str, candidates: list[StaticPromptCandidate], *, fallback_min_length: int = 80
) -> tuple[StaticPromptMatch, ...]:
    catalog = load_catalog(agent_id)
    exact_index = _exact_index(catalog)
    matches: list[StaticPromptMatch] = []
    for candidate in candidates:
        digest = content_hash(candidate.content)
        exact = exact_index.get(digest)
        if exact:
            matches.append(StaticPromptMatch(candidate, exact, "exact", "normalized-hash", 1.0))
            continue
        if len(normalize_for_match(candidate.content)) < fallback_min_length:
            matches.append(StaticPromptMatch(candidate, None, "unknown", "below fallback length", 0.0))
            continue
        matches.append(_best_fallback_match(candidate, catalog))
    return tuple(matches)


def known_content_hashes(agent_id: str) -> frozenset[str]:
    hashes: set[str] = set()
    for entry in load_catalog(agent_id):
        hashes.update(entry.sample_hashes)
    return frozenset(hashes)


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_match(text).encode("utf-8")).hexdigest()


@lru_cache(maxsize=2048)
def normalize_for_match(text: str) -> str:
    value = text.replace("\r\n", "\n").replace("\r", "\n")
    value = _BUILD_TIME_RE.sub('BUILD_TIME:"<build-time>"', value)
    value = _VERSION_RE.sub("<version>", value)
    value = _HEX_RE.sub("<hex>", value)
    value = _TEMPLATE_EXPR_RE.sub("${}", value)
    value = _MARKDOWN_ESCAPE_RE.sub(r"\1", value)
    lines = [_WHITESPACE_RE.sub(" ", line).rstrip() for line in value.split("\n")]
    return _ALL_WHITESPACE_RE.sub(" ", "\n".join(lines)).strip()


def _sample(raw: dict[str, Any]) -> CatalogSample:
    return CatalogSample(
        version=str(raw.get("version") or ""),
        content=str(raw.get("content") or ""),
        anchors=tuple(str(anchor) for anchor in raw.get("anchors", []) if anchor),
    )


def _exact_index(catalog: tuple[CatalogEntry, ...]) -> dict[str, CatalogEntry]:
    index: dict[str, CatalogEntry] = {}
    for entry in catalog:
        for digest in entry.sample_hashes:
            index[digest] = entry
    return index


def _best_fallback_match(candidate: StaticPromptCandidate, catalog: tuple[CatalogEntry, ...]) -> StaticPromptMatch:
    candidate_text = normalize_for_match(candidate.content)
    best_entry: CatalogEntry | None = None
    best_score = 0.0
    weak_entry: CatalogEntry | None = None
    weak_score = 0

    for entry in catalog:
        if not _sample_probe_matches(candidate_text, entry.anchors):
            continue
        anchor_score = _anchor_score(candidate_text, entry.anchors)
        required = _required_anchor_score(entry.anchors)
        score = anchor_score / max(len(entry.anchors), 1)
        if anchor_score >= required and score > best_score:
            best_entry = entry
            best_score = score
        elif anchor_score >= 2 and anchor_score > weak_score:
            weak_entry = entry
            weak_score = anchor_score

    if best_entry is not None:
        return StaticPromptMatch(candidate, best_entry, "anchor", "anchors", best_score)
    if weak_entry is not None and weak_score >= 3:
        return StaticPromptMatch(candidate, weak_entry, "anchor", "anchors", float(weak_score))
    return StaticPromptMatch(candidate, None, "unknown", "no conservative match", best_score)


def _sample_probe_matches(text: str, anchors: tuple[str, ...]) -> bool:
    probes = _anchor_probes(anchors)
    return any(probe in text for probe in probes)


def _required_anchor_score(anchors: tuple[str, ...]) -> int:
    if not anchors:
        return 1
    return min(len(anchors), 3, max(1, math.ceil(len(anchors) * 0.25)))


def _anchor_score(text: str, anchors: tuple[str, ...]) -> int:
    score = 0
    for normalized in _normalized_anchors(anchors):
        if normalized and normalized in text:
            score += 1
    return score


@lru_cache(maxsize=4096)
def _normalized_anchors(anchors: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(normalize_for_match(anchor) for anchor in anchors if anchor)


@lru_cache(maxsize=4096)
def _anchor_probes(anchors: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalized_anchors(anchors)
    return normalized[: min(3, len(normalized))]
