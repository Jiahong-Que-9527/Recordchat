#!/usr/bin/env python3
"""Normalize manually collected staging sources into final data/raw folders."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw"
STAGING_ROOT = RAW_ROOT / "_staging"
TODAY = date.today().isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(clean_text(content) + "\n", encoding="utf-8")


def write_meta(
    target: Path,
    *,
    source_name: str,
    version: str,
    url: str,
    document_type: str,
    domain: str,
    registry_id: str,
    batch_id: str,
) -> None:
    meta = {
        "source_name": source_name,
        "version": version,
        "url": url,
        "document_type": document_type,
        "domain": domain,
        "registry_id": registry_id,
        "batch_id": batch_id,
        "ingested_at": TODAY,
    }
    meta_path = target.with_suffix(target.suffix + ".meta.json")
    ensure_parent(meta_path)
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def html_to_markdown(source: Path, title_override: str | None = None) -> str:
    soup = BeautifulSoup(source.read_text(encoding="utf-8", errors="ignore"), "html.parser")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = title_override
    if not title:
        title_tag = soup.find("title")
        title = title_tag.get_text(" ", strip=True) if title_tag else source.stem

    lines: list[str] = [f"# {title}"]

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        lines.append("")
        lines.append(meta_desc["content"].strip())

    main = soup.find("main") or soup.find("article") or soup.body or soup
    seen: set[str] = set()
    allowed = {"h1", "h2", "h3", "p", "li"}
    for element in main.find_all(allowed):
        text = clean_text(element.get_text(" ", strip=True))
        if len(text) < 20 or text in seen:
            continue
        seen.add(text)
        if element.name == "h1":
            lines.extend(["", f"## {text}"])
        elif element.name == "h2":
            lines.extend(["", f"## {text}"])
        elif element.name == "h3":
            lines.extend(["", f"### {text}"])
        elif element.name == "li":
            lines.append(f"- {text}")
        else:
            lines.extend(["", text])

    return "\n".join(lines)


def pdf_to_markdown(source: Path, title: str) -> str:
    reader = PdfReader(str(source))
    lines = [f"# {title}", "", f"Source file: `{source.name}`", ""]
    for index, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if not text:
            continue
        lines.append(f"## Page {index}")
        lines.append("")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def relative_copy(source: Path, source_root: Path, dest_root: Path) -> Path:
    target = dest_root / source.relative_to(source_root)
    ensure_parent(target)
    target.write_bytes(source.read_bytes())
    return target


def normalize_iata_business_materials() -> None:
    source_root = STAGING_ROOT / "iata_business_materials"
    overview_dir = RAW_ROOT / "one_record_docs" / "overview"
    pdf_dir = RAW_ROOT / "one_record_docs" / "pdfs"

    overview_source = source_root / "overview-page.html"
    overview_target = overview_dir / "iata_one_record_overview.md"
    write_text(overview_target, html_to_markdown(overview_source, "IATA - ONE Record"))
    write_meta(
        overview_target,
        source_name="IATA ONE Record overview page",
        version="captured-page",
        url="https://www.iata.org/en/programs/cargo/e/one-record/",
        document_type="overview_markdown",
        domain="one_record_overview",
        registry_id="manual_iata_and_community_pages",
        batch_id="iata_overview_and_pdf_captures",
    )

    pdf_urls = {
        "data-insight-one-record-data-model.pdf": "https://www.iata.org/contentassets/one-record-data-model/",
        "fact-sheet-one-record.pdf": "https://www.iata.org/contentassets/fact-sheet-one-record/",
        "iata_one_record_implementationplaybook.pdf": "https://www.iata.org/contentassets/one-record-implementation-playbook/",
        "iata_one_record_presentation_en.pdf": "https://www.iata.org/contentassets/one-record-presentation/",
        "iata_one_record_standard_development_dashboard.pdf": "https://www.iata.org/contentassets/one-record-standard-development-dashboard/",
        "one_record_tech_insight_api.pdf": "https://www.iata.org/contentassets/one-record-tech-insight-api/",
    }

    for source in sorted(source_root.glob("*.pdf")):
        target = pdf_dir / (source.stem + ".md")
        title = source.stem.replace("_", " ").replace("-", " ").strip()
        write_text(target, pdf_to_markdown(source, title.title()))
        write_meta(
            target,
            source_name=f"IATA PDF capture: {source.name}",
            version="captured-pdf",
            url=pdf_urls.get(source.name, "manual_pdf_capture"),
            document_type="pdf_text_extract",
            domain="one_record_reference_material",
            registry_id="manual_iata_and_community_pages",
            batch_id="iata_overview_and_pdf_captures",
        )


def normalize_community_narrative() -> None:
    source_root = STAGING_ROOT / "community_narrative_addons"
    notes_root = RAW_ROOT / "notes" / "community_resources"
    examples_root = RAW_ROOT / "examples" / "community"

    source_urls = source_root / "SOURCE_URLS.md"
    notes_target = notes_root / "community_narrative_sources.md"
    write_text(notes_target, source_urls.read_text(encoding="utf-8"))
    write_meta(
        notes_target,
        source_name="Community narrative source notes",
        version="2026-06-07-capture",
        url="mixed_manual_sources",
        document_type="source_notes",
        domain="community_resources",
        registry_id="manual_iata_and_community_pages",
        batch_id="community_narrative_materials",
    )

    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        if any(part.startswith(".") for part in source.relative_to(source_root).parts):
            continue
        if source.name.startswith("."):
            continue
        if source.name == "SOURCE_URLS.md":
            continue

        if source.suffix.lower() == ".html":
            relative = source.relative_to(source_root)
            if "example_payloads" in relative.parts:
                target_root = examples_root
            else:
                target_root = notes_root
            target = (target_root / relative).with_suffix(".md")
            title = source.stem.replace("_", " ").replace("-", " ").strip()
            write_text(target, html_to_markdown(source, title.title()))
            write_meta(
                target,
                source_name=f"Community HTML capture: {relative.as_posix()}",
                version="captured-page",
                url="mixed_manual_sources",
                document_type="html_capture_normalized",
                domain="community_resources",
                registry_id="manual_iata_and_community_pages",
                batch_id="community_narrative_materials",
            )
            continue

        if source.suffix.lower() not in {".md", ".json", ".jsonld", ".ttl", ".yaml", ".yml", ".txt"}:
            continue
        if source.name in {"LICENSE", ".gitkeep"}:
            continue

        relative = source.relative_to(source_root)
        if "example_payloads" in relative.parts:
            target_root = examples_root
            domain = "community_examples"
        else:
            target_root = notes_root
            domain = "community_resources"
        target = relative_copy(source, source_root, target_root)
        document_type = {
            ".md": "markdown_note",
            ".json": "json_example",
            ".jsonld": "jsonld_example",
            ".ttl": "ttl_reference",
            ".yaml": "yaml_config",
            ".yml": "yaml_config",
            ".txt": "text_note",
        }[source.suffix.lower()]
        write_meta(
            target,
            source_name=f"Community narrative file: {relative.as_posix()}",
            version="2026-06-07-capture",
            url="mixed_manual_sources",
            document_type=document_type,
            domain=domain,
            registry_id="manual_iata_and_community_pages",
            batch_id="community_narrative_materials",
        )


def main() -> int:
    normalize_iata_business_materials()
    normalize_community_narrative()
    print("Manual source normalization complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
