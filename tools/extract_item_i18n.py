from __future__ import annotations

from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS = Path.home() / "Downloads"
LANG_SOURCES = {
    'en': [DOWNLOADS / 'items.json', DOWNLOADS / 'items2.json'],
    'ja': [DOWNLOADS / 'items_ja.json', DOWNLOADS / 'items2_ja.json'],
}
OUT = ROOT / 'ao_item_i18n.json'


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_json(path: Path):
    raw = path.read_bytes()
    for encoding in ('utf-8-sig', 'cp932', 'shift_jis', 'utf-16'):
        try:
            return json.loads(raw.decode(encoding)), encoding
        except Exception:
            continue
    raise RuntimeError(f'Cannot decode JSON file: {path}')


def load_language_sources(paths):
    by_id = {}
    conflicts = []
    encodings = {}
    for source in paths:
        raw, encoding = read_json(source)
        encodings[source.name] = encoding
        for row in raw:
            code = int(row['id'])
            source_name = source.name
            if code in by_id:
                old = by_id[code]
                if old.get('name') != row.get('name') or old.get('desc') != row.get('desc'):
                    conflicts.append({
                        'id_hex': f'0x{code:04X}',
                        'previous_source': old.get('source_file'),
                        'new_source': source_name,
                        'previous_name': old.get('name'),
                        'new_name': row.get('name'),
                    })
            by_id[code] = {**row, 'source_file': source_name}
    return by_id, conflicts, encodings


def main():
    items_mod = load_module('ao_items_db_for_i18n', ROOT / 'ao_items_db.py')
    item_ids = set(items_mod.ITEM_DB)
    loaded = {}
    meta_languages = {}
    for lang, sources in LANG_SOURCES.items():
        by_id, conflicts, encodings = load_language_sources(sources)
        loaded[lang] = by_id
        meta_languages[lang] = {
            'sources': [source.name for source in sources],
            'encodings': encodings,
            'source_total': len(by_id),
            'matched_total': len(item_ids & set(by_id)),
            'with_name_total': sum(1 for code in item_ids & set(by_id) if by_id[code].get('name')),
            'missing_item_db_ids': [f'0x{code:04X}' for code in sorted(item_ids - set(by_id))],
            'extra_source_ids': [f'0x{code:04X}' for code in sorted(set(by_id) - item_ids)],
            'conflicts': conflicts,
        }

    matched = []
    for code, (category, zh_cn) in sorted(items_mod.ITEM_DB.items()):
        en = loaded['en'].get(code, {})
        ja = loaded['ja'].get(code, {})
        if not en and not ja:
            continue
        matched.append({
            'id_hex': f'0x{code:04X}',
            'id_dec': code,
            'category': category,
            'zh_cn': zh_cn,
            'en': en.get('name') or '',
            'en_desc': en.get('desc') or '',
            'en_source': en.get('source_file') or '',
            'ja': ja.get('name') or '',
            'ja_desc': ja.get('desc') or '',
            'ja_source': ja.get('source_file') or '',
        })

    data = {
        'meta': {
            'title': 'Ao no Kiseki / Trails to Azure item localization candidates',
            'languages': meta_languages,
            'item_db_total': len(items_mod.ITEM_DB),
            'matched_any_language_total': len(matched),
            'match_rule': 'Direct match by numeric item id.',
            'notes': [
                'English and Japanese names come from the user-provided item JSON files.',
                'Rows absent from the source files are intentionally left untranslated.',
                'Descriptions are retained in JSON for reference but not rendered in the Markdown glossary.',
            ],
        },
        'items': matched,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(OUT)
    print(json.dumps(data['meta'], ensure_ascii=False))


if __name__ == '__main__':
    main()
