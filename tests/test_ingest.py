# Tests for Markdown ingestion and the generated chunks file.

import json
from pathlib import Path

from src.ingest import build_chunks, parse_heading, split_sections

CHUNKS_FILE = Path("data/chunks.jsonl")


def load_saved_chunks():
    """Read the real chunks file produced by src.ingest.main()."""
    with CHUNKS_FILE.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_parse_heading_rejects_hashtag_and_deep_headings():
    assert parse_heading("#hashtag") is None
    assert parse_heading("#### too deep") is None
    assert parse_heading("##### still too deep") is None


def test_heading_inside_code_fence_is_not_a_section():
    markdown = """# Real heading

Text before code.

```
# Inside code
```

## Second heading

Text after code.
"""
    sections = split_sections(markdown)
    assert [heading for heading, _ in sections] == ["Real heading", "Real heading > Second heading"]
    # The line stays in the code block body, but it must not become a heading.
    assert "# Inside code" in sections[0][1]
    assert all("Inside code" not in heading for heading, _ in sections)


def test_saved_chunks_have_even_fence_markers():
    for chunk in load_saved_chunks():
        assert chunk["text"].count("```") % 2 == 0, chunk["chunk_id"]


def test_saved_chunks_have_heading_path_and_section_key():
    for chunk in load_saved_chunks():
        assert chunk["heading_path"].strip()
        assert chunk["section_key"].strip()
        assert chunk["source_path"] in chunk["section_key"]


def test_saved_chunk_ids_are_unique():
    ids = [chunk["chunk_id"] for chunk in load_saved_chunks()]
    assert len(ids) == len(set(ids))


def test_build_chunks_is_deterministic(tmp_path):
    first = tmp_path / "a.md"
    first.write_text("# Same title\n\nHello world.\n", encoding="utf-8")
    assert build_chunks(tmp_path) == build_chunks(tmp_path)


def test_same_heading_in_two_files_gets_two_section_keys(tmp_path):
    (tmp_path / "one.md").write_text("# Same title\n\nFirst file.\n", encoding="utf-8")
    (tmp_path / "two.md").write_text("# Same title\n\nSecond file.\n", encoding="utf-8")

    chunks = build_chunks(tmp_path)
    keys = [chunk["section_key"] for chunk in chunks]
    assert len(set(keys)) == 2
    assert all("::" in key for key in keys)
