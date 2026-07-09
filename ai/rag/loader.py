"""Parse ai/knowledge_base/INDEX.md as the ingestion manifest and load
each referenced Markdown document into H1/H2-delimited sections.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"
INDEX_PATH = KB_DIR / "INDEX.md"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_TABLE_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(\w+)\s*\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|\s*$"
)
_H1_RE = re.compile(r"^#\s+(.*)$")
_H2_RE = re.compile(r"^##\s+(.*)$")


@dataclass
class ManifestEntry:
    doc_id: int
    title: str
    doc_type: str
    source_path: str
    description: str


@dataclass
class Section:
    heading: str
    content: str


@dataclass
class Document:
    doc_id: int
    title: str
    doc_type: str
    source_path: str
    sections: list[Section] = field(default_factory=list)


def parse_manifest(index_path: Path = INDEX_PATH) -> list[ManifestEntry]:
    """Read the `| # | Title | doc_type | source_path | Description |` table in INDEX.md."""
    entries: list[ManifestEntry] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        match = _TABLE_ROW_RE.match(line.strip())
        if not match:
            continue
        doc_id_str, title, doc_type, source_path, description = match.groups()
        entries.append(
            ManifestEntry(
                doc_id=int(doc_id_str),
                title=title,
                doc_type=doc_type,
                source_path=source_path,
                description=description,
            )
        )
    return entries


def parse_document_body(text: str, fallback_title: str) -> list[Section]:
    """Split a document's body into sections keyed by its H2 headings.

    Content before the first H2 (including the H1 title line) is kept
    under an "Overview" section so nothing is dropped from chunking.
    """
    sections: list[Section] = []
    current_heading = "Overview"
    current_lines: list[str] = []

    def flush() -> None:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(Section(heading=current_heading, content=content))

    for line in text.splitlines():
        if _H1_RE.match(line):
            continue
        h2 = _H2_RE.match(line)
        if h2:
            flush()
            current_heading = h2.group(1).strip()
            current_lines = []
            continue
        current_lines.append(line)
    flush()
    return sections


def load_document(entry: ManifestEntry, repo_root: Path = REPO_ROOT) -> Document:
    doc_path = repo_root / entry.source_path
    text = doc_path.read_text(encoding="utf-8")
    sections = parse_document_body(text, fallback_title=entry.title)
    return Document(
        doc_id=entry.doc_id,
        title=entry.title,
        doc_type=entry.doc_type,
        source_path=entry.source_path,
        sections=sections,
    )


def load_all_documents(
    repo_root: Path = REPO_ROOT, index_path: Path = INDEX_PATH
) -> list[Document]:
    entries = parse_manifest(index_path)
    return [load_document(entry, repo_root) for entry in entries]
