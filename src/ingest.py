# Turn the raw Markdown docs into clean, cited chunks with stable IDs.

import json
import re
from pathlib import Path

ROOT = Path("data/raw")
CHUNKS_PATH = Path("data/chunks.jsonl")
MAX_WORDS = 400

# split_long_sections() fills this so main() can report oversized code blocks.
LARGE_CODE_BLOCKS = []


def find_markdown_files(root):
    """Return a sorted list of Markdown files under root."""
    root = Path(root)
    return sorted(path for path in root.rglob("*.md") if path.is_file())


def parse_heading(line):
    """Return (level, title) for an H1-H3 line, or None for anything else."""
    # Only 1-3 '#' followed by whitespace counts; '#hashtag' and '#### x' do not.
    match = re.match(r"^(#{1,3})\s+(.*)$", line)
    if not match:
        return None
    level = len(match.group(1))
    title = match.group(2)
    # Remove the site-specific heading anchor, e.g. ' { #first-steps }'.
    title = re.sub(r"\s*\{\s*#[^}]*\}\s*$", "", title).strip()
    return level, title


def _fence_marker(line):
    """Return the fence marker type for a line that opens or closes a fence."""
    stripped = line.strip()
    if stripped.startswith("```"):
        return "```"
    if stripped.startswith("~~~"):
        return "~~~"
    return None


def _fence_info(line):
    """Return text after a fence marker; a closing fence has no info."""
    marker = _fence_marker(line)
    if not marker:
        return ""
    return line.strip()[len(marker):].strip()


def split_sections(md_text):
    """Return (heading_path, body) pairs; never split inside a code fence."""
    sections = []
    heading_parts = []
    body_lines = []
    in_fence = False
    fence_marker = None

    def flush():
        if body_lines:
            sections.append((" > ".join(heading_parts), "\n".join(body_lines).strip()))

    for line in md_text.splitlines():
        marker = _fence_marker(line)
        if in_fence:
            # Code fence lines are copied unchanged, including blank lines.
            body_lines.append(line)
            if marker == fence_marker and not _fence_info(line):
                in_fence = False
            continue

        if marker:
            in_fence = True
            fence_marker = marker
            body_lines.append(line)
            continue

        heading = parse_heading(line)
        if heading:
            flush()
            level, title = heading
            # A new heading keeps its ancestors and drops same-level/deeper ones.
            heading_parts = heading_parts[: level - 1] + [title]
            body_lines = []
        else:
            body_lines.append(line)

    flush()
    return sections


def _paragraph_units(body):
    """Group lines into paragraph-sized units, keeping code fences whole."""
    units = []
    current = []
    in_fence = False
    fence_marker = None

    for line in body.splitlines():
        marker = _fence_marker(line)
        if in_fence:
            current.append(line)
            if marker == fence_marker and not _fence_info(line):
                in_fence = False
            continue

        if marker:
            in_fence = True
            fence_marker = marker
            current.append(line)
            continue

        if line.strip() == "":
            if current:
                units.append("\n".join(current).strip())
                current = []
        else:
            current.append(line)

    if current:
        units.append("\n".join(current).strip())
    return [unit for unit in units if unit]


def _is_code_unit(unit):
    """True when a unit starts with a code fence line."""
    first = next((line for line in unit.splitlines() if line.strip()), "")
    return _fence_marker(first) is not None


def _word_count(text):
    """Simple whitespace word count, used for all size checks."""
    return len(text.split())


def _overlap_units(units, overlap_words):
    """Take whole trailing prose paragraphs up to overlap_words words."""
    if overlap_words <= 0:
        return []
    picked = []
    total = 0
    for unit in reversed(units):
        # Never start overlap inside a code block: that would split its fences.
        if _is_code_unit(unit):
            break
        words = _word_count(unit)
        if total + words > overlap_words:
            break
        picked.append(unit)
        total += words
    return list(reversed(picked))


def split_long_sections(body, min_words=250, max_words=400, overlap_words=50):
    """Split a section on blank lines into roughly 250-400 word chunks."""
    units = _paragraph_units(body)
    chunks = []
    current = []
    current_words = 0

    for unit in units:
        words = _word_count(unit)

        # A single oversized code block is kept whole and reported to main().
        if _is_code_unit(unit) and words > max_words:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_words = 0
            LARGE_CODE_BLOCKS.append(unit)
            chunks.append(unit)
            continue

        # Only split after we have enough words, so chunks are not tiny.
        if current and current_words + words > max_words and current_words >= min_words:
            chunks.append("\n\n".join(current))
            current = _overlap_units(current, overlap_words)
            current_words = sum(_word_count(item) for item in current)

        current.append(unit)
        current_words += words

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def clean_text(text):
    """Remove MkDocs-only syntax outside code fences; keep code unchanged."""
    lines = text.splitlines()

    # Rule 1: drop YAML front matter at the very top of a file.
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                lines = lines[index + 1:]
                break

    cleaned = []
    in_fence = False
    fence_marker = None
    skip_mermaid = False
    skip_directive = False
    skip_style = False

    for line in lines:
        marker = _fence_marker(line)

        if in_fence:
            # Rule 2: code block contents stay byte-for-byte unchanged.
            if skip_mermaid:
                # Rule 3: drop mermaid diagram blocks entirely (not searchable text).
                if marker == fence_marker and not _fence_info(line):
                    in_fence = False
                    fence_marker = None
                    skip_mermaid = False
                continue
            cleaned.append(line)
            if marker == fence_marker and not _fence_info(line):
                in_fence = False
                fence_marker = None
            continue

        if marker:
            info = _fence_info(line)
            if info.lower() == "mermaid":
                # Rule 3: start dropping a mermaid block.
                in_fence = True
                fence_marker = marker
                skip_mermaid = True
                continue
            if info and (info.startswith("hl_lines") or info.startswith("{")):
                # Rule 4: normalize highlight/annotation openers to a plain fence.
                cleaned.append(marker)
            else:
                cleaned.append(line)
            in_fence = True
            fence_marker = marker
            continue

        if skip_directive:
            # Rule 5: drop mkdocstrings directives and their indented options.
            if line.strip() == "":
                skip_directive = False
                continue
            if line[:1].isspace():
                continue
            skip_directive = False

        if skip_style:
            # Rule 6: drop <style> blocks (presentation only).
            if re.match(r"^\s*</style>", line):
                skip_style = False
            continue

        stripped = line.strip()

        if stripped.startswith(":::"):
            skip_directive = True
            continue
        if re.match(r"^\s*<style\b", line):
            skip_style = True
            continue
        if re.match(r"^\{\*.*\*\}$", stripped):
            # Rule 7: drop '{* ../../docs_src/... *}' source includes.
            continue
        admonition = re.match(r"^\s*///\s*(.*?)\s*$", line)
        if admonition:
            # Rule 8: convert '/// tip' / '/// note | Technical Details' to a
            # plain label line, and drop the bare '///' closing marker.
            label = admonition.group(1).strip()
            if not label:
                continue
            if "|" in label:
                label = label.split("|", 1)[1].strip()
            else:
                label = label[:1].upper() + label[1:]
            cleaned.append(f"{label}:")
            continue
        if stripped in {"<div class=\"termy\">", "</div>", "<details>", "</details>"}:
            # Rule 9: drop terminal/collapsible HTML wrappers.
            continue
        summary = re.match(r"^\s*<summary>(.*)</summary>\s*$", line)
        if summary:
            # Rule 9: keep the visible text of a <summary> line.
            cleaned.append(summary.group(1))
            continue
        if re.match(r"^\s*<img\b[^>]*>\s*$", line):
            # Rule 9: drop image tags; image files are outside the text corpus.
            continue

        # Rule 10: strip common inline site HTML outside code fences.
        line = re.sub(r"</?(?:font|span|em|a|p|br|strong|code)\b[^>]*>", "", line)
        # Rule 11: remove heading anchors such as ' { #first-steps }'.
        line = re.sub(r"\s*\{\s*#[^}]*\}\s*$", "", line)
        cleaned.append(line)

    return "\n".join(cleaned).strip()


def build_chunks(root=ROOT):
    """Build cited chunks from Markdown files; IDs are stable across runs."""
    global LARGE_CODE_BLOCKS
    LARGE_CODE_BLOCKS = []

    root = Path(root)
    chunks = []

    for path in find_markdown_files(root):
        source_path = path.relative_to(root).as_posix()
        cleaned = clean_text(path.read_text(encoding="utf-8"))
        sections = split_sections(cleaned)
        if not sections:
            # Files with no headings (for example a banner) get a stem label.
            sections = [(Path(source_path).stem, cleaned)]

        # One counter per file keeps IDs unique even when a file repeats a heading.
        file_index = 0
        for heading_path, body in sections:
            heading_path = heading_path or Path(source_path).stem
            section_key = f"{source_path} :: {heading_path}"
            for part in split_long_sections(body):
                text = f"{heading_path}\n\n{part}".strip()
                chunks.append({
                    "chunk_id": f"{source_path}#{file_index}",
                    "section_key": section_key,
                    "source_path": source_path,
                    "heading_path": heading_path,
                    "word_count": _word_count(text),
                    "text": text,
                })
                file_index += 1

    return chunks


def main():
    """Write data/chunks.jsonl and print corpus counts."""
    chunks = build_chunks(ROOT)
    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CHUNKS_PATH.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"files: {len(find_markdown_files(ROOT))}")
    print(f"sections: {len({chunk['section_key'] for chunk in chunks})}")
    print(f"chunks: {len(chunks)}")
    print(f"chunks over max_words: {sum(1 for c in chunks if c['word_count'] > MAX_WORDS)}")
    print(f"code blocks over max_words: {len(LARGE_CODE_BLOCKS)}")


if __name__ == "__main__":
    main()
