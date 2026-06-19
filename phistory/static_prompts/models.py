from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class StaticPromptCandidate:
    id: str
    content: str
    kind: str
    score: int
    order: int
    variables: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogSample:
    version: str
    content: str
    anchors: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    name: str
    description: str
    category: str
    samples: tuple[CatalogSample, ...]
    anchors: tuple[str, ...] = ()
    sample_hashes: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class StaticPromptMatch:
    candidate: StaticPromptCandidate
    entry: CatalogEntry | None
    confidence: str
    reason: str
    similarity: float = 0.0


@dataclass(frozen=True)
class StaticPromptResult:
    agent_id: str
    version: str
    source: str
    matches: tuple[StaticPromptMatch, ...]

    @property
    def known_count(self) -> int:
        return sum(1 for match in self.matches if match.entry is not None)

    @property
    def unknown_count(self) -> int:
        return len(self.matches) - self.known_count


@dataclass(frozen=True)
class StaticCandidatesResult:
    agent_id: str
    version: str
    source: str
    extractor: str
    min_length: int
    candidates: tuple[StaticPromptCandidate, ...]
