#!/usr/bin/env python3
"""
Fetch raw English/Japanese name candidates from Kiseki Wiki Azure list pages.

The output intentionally does not assign save item IDs. It preserves page,
section, English name, Japanese name, and nearby context so a later alignment
step can match these names against the existing Joyoland/BZH Chinese database.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote


PAGES = {
    "weapons": "https://kiseki.fandom.com/wiki/List_of_weapons_(Azure)",
    "armor": "https://kiseki.fandom.com/wiki/List_of_armor_(Azure)",
    "car_items": "https://kiseki.fandom.com/wiki/List_of_car_items_(Azure)",
    "crafts": "https://kiseki.fandom.com/wiki/List_of_crafts_(Azure)",
    "master_quartz": "https://kiseki.fandom.com/wiki/List_of_master_quartz_(Azure)",
    "quartz": "https://kiseki.fandom.com/wiki/List_of_quartz_(Azure)",
    "fishing_equipment": "https://kiseki.fandom.com/wiki/List_of_fishing_equipment_(Azure)",
    "enemies": "https://kiseki.fandom.com/wiki/List_of_enemies_(Azure)",
    "fish": "https://kiseki.fandom.com/wiki/List_of_fish_(Azure)",
    "books": "https://kiseki.fandom.com/wiki/List_of_books_(Azure)",
    "achievements": "https://kiseki.fandom.com/wiki/List_of_achievements_(Azure)",
}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AoSaveEditorDataCollector/1.0"
JA_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
BOLD_NAME_RE = re.compile(r"_*\s*\*\*(?P<en>[^*]+?)\*\*_?\s*(?P<ja>[\u3040-\u30ff\u3400-\u9fff][^|]*)")
NOISE = {
    "Name",
    "Description",
    "Location",
    "Acquire",
    "Cost",
    "Delay",
    "Power",
    "Targets/Effect",
    "Contents",
    "References",
    "Notes",
    "Image",
    "---",
}


def markdown_url(url: str) -> str:
    return f"https://markdown.new/{quote(url, safe=':/()_')}?method=ai"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/markdown,*/*"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean_text(text: str) -> str:
    text = re.sub(r"\[\s*\d+\s*\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def markdown_lines(markdown: str) -> list[dict[str, str]]:
    lines: list[dict[str, str]] = []
    current_heading = ""
    for raw in markdown.splitlines():
        text = raw.strip()
        if not text:
            continue
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text).strip()
        text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text).strip()
        text = text.strip("| ")
        if not text:
            continue
        if text.startswith("#"):
            current_heading = text.lstrip("#").strip()
            lines.append({"kind": "heading", "section": current_heading, "text": current_heading})
            continue
        cells = [cell.strip() for cell in text.split("|") if cell.strip()]
        if len(cells) > 1:
            for cell in cells:
                lines.append({"kind": "cell", "section": current_heading, "text": cell})
        else:
            lines.append({"kind": "text", "section": current_heading, "text": text})
    return lines


def extract_entries(lines: list[dict[str, str]]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    pending_en: dict[str, object] | None = None
    recent: list[str] = []

    for line in lines:
        text = clean_text(line["text"])
        section = line["section"]
        if not text or text in NOISE:
            continue
        if line["kind"] == "heading":
            recent.clear()
            pending_en = None
            continue

        bold_matches = list(BOLD_NAME_RE.finditer(text))
        bold_name = bold_matches[-1] if bold_matches else None
        if bold_name and JA_RE.search(bold_name.group("ja")):
            entries.append({
                "section": section,
                "en": clean_text(bold_name.group("en")),
                "ja": clean_text(bold_name.group("ja")),
                "context": recent[-4:],
            })
            pending_en = None
            recent.append(text)
            if len(recent) > 8:
                recent.pop(0)
            continue

        has_ja = bool(JA_RE.search(text))
        looks_separator = bool(re.fullmatch(r"[-: ]+", text))
        looks_stat = bool(re.search(r"\b(STR|DEF|ADF|ATS|SPD|HP|EP|CP|ACC|EVA|MOV|RNG|AT)\b|^\d+(\.\d+)?\s*s$", text))
        looks_sentence = len(text.split()) > 10 or text.endswith(".")
        looks_url_meta = text.startswith(("Title:", "URL Source:", "Markdown Content:"))

        if has_ja and pending_en and not looks_sentence:
            pending_en["ja"] = text
            pending_en["context"] = recent[-4:]
            entries.append(pending_en)
            pending_en = None
        elif (
            not has_ja
            and not looks_stat
            and not looks_sentence
            and not looks_separator
            and not looks_url_meta
            and 1 <= len(text) <= 90
        ):
            pending_en = {"section": section, "en": text, "ja": None, "context": []}

        recent.append(text)
        if len(recent) > 8:
            recent.pop(0)

    return entries


def main() -> int:
    out_path = Path(__file__).resolve().parent.parent / "wiki_azure_names_raw.json"
    result: dict[str, object] = {
        "source": "Kiseki Wiki / Fandom via markdown.new",
        "note": "Raw English/Japanese candidates only. Save item IDs are not assigned here.",
        "pages": {},
    }

    for key, url in PAGES.items():
        fetch_url = markdown_url(url)
        print(f"fetch {key}: {fetch_url}", file=sys.stderr)
        markdown = fetch(fetch_url)
        lines = markdown_lines(markdown)
        entries = extract_entries(lines)
        result["pages"][key] = {
            "url": url,
            "fetch_url": fetch_url,
            "line_count": len(lines),
            "entry_count": len(entries),
            "raw_lines": lines,
            "entries": entries,
        }
        time.sleep(0.5)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
