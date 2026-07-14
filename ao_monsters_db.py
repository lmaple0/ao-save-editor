"""Validated localized monster reference catalog for Ao Save Editor."""

from dataclasses import dataclass
import json
import os


MONSTER_REFERENCE_SCHEMA_VERSION = 3
SUPPORTED_LOCALES = ("zh_cle", "ja", "en")
UI_LOCALE_MAP = {"zh_cn": "zh_cle", "ja": "ja", "en": "en"}


def _parse_code(value):
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value, 0)
    raise TypeError(f"unsupported monster code: {value!r}")


def _data_locale(locale):
    return UI_LOCALE_MAP.get(str(locale or "zh_cn"), "zh_cle")


@dataclass(frozen=True)
class MonsterReference:
    save_code: int
    dbmon_id: int
    ms_file: str
    zh_joyoland: str
    zh_cle: str
    ja: str
    en: str
    level: int
    source_status: str
    verified_for_nisa_save: bool
    locations_zh_cle: tuple
    locations_ja: tuple
    locations_en: tuple
    location_source: str
    location_map_indexes: tuple
    location_scene_files: tuple

    @property
    def save_code_hex(self):
        return f"0x{self.save_code:08X}"

    @property
    def dbmon_id_hex(self):
        return f"0x{self.dbmon_id:04X}"

    def name(self, locale="zh_cn"):
        return getattr(self, _data_locale(locale))

    def locations(self, locale="zh_cn"):
        return getattr(self, f"locations_{_data_locale(locale)}")

    @classmethod
    def from_dict(cls, row):
        required = {
            "save_code", "dbmon_id", "ms_file", "zh_joyoland", "zh_cle", "ja", "en",
            "level", "source_status", "verified_for_nisa_save", "location_source",
            "location_map_indexes", "location_scene_files",
            *(f"locations_{locale}" for locale in SUPPORTED_LOCALES),
        }
        missing = sorted(required - set(row))
        if missing:
            raise ValueError(f"monster reference is missing fields: {', '.join(missing)}")
        status = str(row["source_status"])
        if status not in {"active", "commented"}:
            raise ValueError(f"unsupported monster source status: {status}")
        ms_file = str(row["ms_file"])
        if not (ms_file.startswith("ms") and ms_file.endswith(".dat")):
            raise ValueError(f"invalid monster status filename: {ms_file}")
        names = {locale: str(row[locale]).strip() for locale in SUPPORTED_LOCALES}
        if any(not value for value in names.values()):
            raise ValueError(f"localized monster name is empty: {ms_file}")
        locations = {
            locale: tuple(str(value).strip() for value in row[f"locations_{locale}"])
            for locale in SUPPORTED_LOCALES
        }
        if any(not values or any(not value for value in values) for values in locations.values()):
            raise ValueError(f"localized monster locations are empty: {ms_file}")
        location_source = str(row["location_source"])
        if location_source not in {"nisa_pc_scenario_scan", "local_town_name_supplement"}:
            raise ValueError(f"unsupported monster location source: {location_source}")
        return cls(
            save_code=_parse_code(row["save_code"]), dbmon_id=_parse_code(row["dbmon_id"]),
            ms_file=ms_file, zh_joyoland=str(row["zh_joyoland"]), **names,
            level=int(row["level"]), source_status=status,
            verified_for_nisa_save=bool(row["verified_for_nisa_save"]),
            **{f"locations_{locale}": values for locale, values in locations.items()},
            location_source=location_source,
            location_map_indexes=tuple(int(value) for value in row["location_map_indexes"]),
            location_scene_files=tuple(str(value) for value in row["location_scene_files"]),
        )


class MonsterCatalog:
    """Deep module that owns catalog loading, localization, lookup, and search."""

    def __init__(self, records=(), metadata=None):
        records = tuple(records)
        by_code = {}
        for record in records:
            if not isinstance(record, MonsterReference):
                raise TypeError("records must contain MonsterReference values")
            if record.save_code in by_code:
                raise ValueError(f"duplicate monster code: {record.save_code_hex}")
            by_code[record.save_code] = record
        self._records = records
        self._by_code = by_code
        self.metadata = dict(metadata or {})

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict):
            raise ValueError("monster reference root must be an object")
        if data.get("schema_version") != MONSTER_REFERENCE_SCHEMA_VERSION:
            raise ValueError(f"unsupported monster reference schema: {data.get('schema_version')!r}")
        rows = data.get("monsters")
        if not isinstance(rows, list):
            raise ValueError("monster reference monsters must be a list")
        records = [MonsterReference.from_dict(row) for row in rows]
        return cls(records, {key: value for key, value in data.items() if key != "monsters"})

    def __len__(self):
        return len(self._records)

    def get(self, code):
        return self._by_code.get(_parse_code(code))

    def records(self):
        return self._records

    def locations(self, locale="zh_cn"):
        return tuple(sorted({location for record in self._records for location in record.locations(locale)}, key=str.casefold))

    def search(self, query, location=None, locale="zh_cn"):
        query = str(query or "").strip().casefold()
        location = str(location or "").strip()
        matches = []
        for record in self._records:
            localized_locations = record.locations(locale)
            if location and not any(candidate == location or candidate.startswith(location + " / ") for candidate in localized_locations):
                continue
            all_locations = tuple(location for data_locale in SUPPORTED_LOCALES for location in record.locations(data_locale))
            text = " ".join((record.save_code_hex, record.dbmon_id_hex, record.ms_file,
                             record.zh_joyoland, record.zh_cle, record.ja, record.en,
                             str(record.level), record.source_status, *all_locations)).casefold()
            if not query or query in text:
                matches.append(record)
        return tuple(matches)

    def compare_codes(self, expected_codes):
        expected = {_parse_code(code) for code in expected_codes}
        actual = set(self._by_code)
        return {"missing": tuple(sorted(expected - actual)), "extra": tuple(sorted(actual - expected))}


def load_default_monster_catalog(base_dir=None):
    base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
    try:
        return MonsterCatalog.load(os.path.join(base_dir, "ao_monster_reference.json"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return MonsterCatalog()
