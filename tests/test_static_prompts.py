from phistory.static_prompts.catalog import load_catalog, match_candidates, normalize_for_match
from phistory.static_prompts.extract import _keep_known_or_prompt_like, read_static_candidates, write_static_candidates
from phistory.static_prompts.javascript import extract_prompt_candidates, extract_string_candidates
from phistory.static_prompts.models import StaticCandidatesResult


def test_javascript_prompt_extraction_skips_comments_and_matches_known_catalog():
    entry = next(item for item in load_catalog("claude-code") if item.id == "agent-auto-mode-rule-reviewer")
    content = "\n\n".join(entry.anchors[:3])
    source = "\n".join(
        [
            "// You are not a real prompt in a comment.",
            "const small = 'You are too short';",
            f"const prompt = {content!r};",
        ]
    )

    candidates = extract_prompt_candidates(source)
    matches = match_candidates("claude-code", candidates)

    assert len(candidates) == 1
    assert matches[0].entry is not None
    assert matches[0].entry.id == "agent-auto-mode-rule-reviewer"
    assert matches[0].confidence == "anchor"


def test_javascript_prompt_extraction_filters_static_resources():
    source = "\n".join(
        [
            "const regex = '\\\\b(ll(AgentInExperience|CreateKeyValue|DeleteKeyValue|Sin|Cos|Tan))';",
            "const tokens = 'ABS ACCRINT ACCRINTM ACOS ACOSH ACOT ACOTH AGGREGATE ADDRESS AMORDEGRC AMORLINC AND ARABIC AREAS ASC ASIN ASINH ATAN ATAN2 ATANH AVEDEV AVERAGE AVERAGEA AVERAGEIF';",
            "const source = `// Shared filesystem + string helpers used across the converter modules.\\n// Pure functions only -- no process globals, no CLI parsing.\\nimport { existsSync, readFileSync } from 'node:fs';\\nimport { dirname, join } from 'node:path';`;",
            'const html = `<!DOCTYPE html><html><head><style>.at-a-glance { color: red; }</style></head><body><div class="at-a-glance">${value}</div><section>${other}</section></body></html>`;',
            "const prompt = `You are an expert reviewer of auto mode classifier rules for Claude Code.\\n\\nYour task is to critique the user's custom rules for clarity, completeness, and potential issues. Be concise and constructive. Only comment on rules that could be improved.`;",
        ]
    )

    candidates = extract_prompt_candidates(source)

    assert len(candidates) == 1
    assert "expert reviewer" in candidates[0].content


def test_known_catalog_matches_are_kept_before_strict_unknown_filtering():
    entry = next(item for item in load_catalog("claude-code") if item.id == "agent-auto-mode-rule-reviewer")
    source = f"const prompt = {' '.join(entry.anchors[:3])!r};"

    raw_matches = match_candidates("claude-code", extract_string_candidates(source, min_length=20))
    kept = _keep_known_or_prompt_like(raw_matches)

    assert len(kept) == 1
    assert kept[0].entry is not None
    assert kept[0].entry.id == entry.id


def test_catalog_matching_normalizes_template_variable_names():
    assert normalize_for_match("Use ${internalName} now") == normalize_for_match("Use ${} now")


def test_static_candidates_roundtrip(tmp_path):
    candidates = tuple(
        extract_string_candidates("const prompt = 'You must write a concise plan for the user.';", min_length=20)
    )
    result = StaticCandidatesResult(
        agent_id="claude-code",
        version="1.2.3",
        source="node_modules/@anthropic-ai/claude-code/bin/claude.exe",
        extractor="test",
        min_length=20,
        candidates=candidates,
    )
    path = tmp_path / "static-candidates.json"

    write_static_candidates(path, result)
    loaded = read_static_candidates(path)

    assert loaded.agent_id == result.agent_id
    assert loaded.version == result.version
    assert loaded.source == result.source
    assert loaded.candidates == result.candidates
