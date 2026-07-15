"""Read-only structural diagnostics for NISA Trails to Azure saves."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import struct

from ao_save_layout import (
    DIFFICULTY_OFFSET,
    EXPECTED_SIZE,
    ITEMS_END,
    ITEMS_START,
    MONSTER_COMPLETE_PAYLOAD,
    MONSTER_END,
    MONSTER_RECORD_SIZE,
    MONSTER_START,
    RECIPE_BOOK_MASK,
    RECIPE_BOOK_OFFSETS,
    ROLE_DISPLAY_OFFSETS,
    TEAM_SLOTS,
)
KNOWN_TEAM_IDS = frozenset((*range(11), 0x00FF))
KNOWN_ROLE_DISPLAY_IDS = frozenset(range(21))


TEXT = {
    "zh_cn": {
        "title": "存档只读诊断报告",
        "overall_clean": "结论：未发现结构异常。",
        "overall_issues": "结论：发现 {errors} 个错误、{warnings} 个警告、{infos} 个提示。",
        "size": "存档：{size} 字节；校验和：{checksum}",
        "valid": "有效",
        "invalid": "不匹配（编辑后会在保存时重算）",
        "unknown": "未检查",
        "items": "物品：{populated}/{capacity} 槽，{unique} 个唯一 ID",
        "monsters": "怪物图鉴：{known}/{total} 已登记，{complete} 全资料，{partial} 部分资料，缺失 {missing}",
        "references": "参考数据：物品 {items} 项；怪物 {monsters} 项；版本 {edition}",
        "issues": "诊断明细：",
        "no_issues": "  无",
        "severity_error": "错误",
        "severity_warning": "警告",
        "severity_info": "提示",
    },
    "en": {
        "title": "Read-only Save Diagnostics",
        "overall_clean": "Result: no structural anomalies found.",
        "overall_issues": "Result: {errors} error(s), {warnings} warning(s), {infos} notice(s).",
        "size": "Save: {size} bytes; checksum: {checksum}",
        "valid": "valid",
        "invalid": "mismatch (recalculated when saved)",
        "unknown": "not checked",
        "items": "Items: {populated}/{capacity} slots, {unique} unique IDs",
        "monsters": "Monster manual: {known}/{total} registered, {complete} complete, {partial} partial, {missing} missing",
        "references": "References: {items} items; {monsters} monsters; edition {edition}",
        "issues": "Findings:",
        "no_issues": "  None",
        "severity_error": "ERROR",
        "severity_warning": "WARNING",
        "severity_info": "INFO",
    },
    "ja": {
        "title": "セーブデータ読み取り専用診断",
        "overall_clean": "結果：構造上の異常は見つかりませんでした。",
        "overall_issues": "結果：エラー {errors} 件、警告 {warnings} 件、情報 {infos} 件。",
        "size": "セーブ：{size} バイト、チェックサム：{checksum}",
        "valid": "正常",
        "invalid": "不一致（保存時に再計算）",
        "unknown": "未確認",
        "items": "アイテム：{populated}/{capacity} スロット、固有 ID {unique} 件",
        "monsters": "魔獣図鑑：登録 {known}/{total}、全データ {complete}、部分 {partial}、未登録 {missing}",
        "references": "参照データ：アイテム {items} 件、魔獣 {monsters} 件、版 {edition}",
        "issues": "診断内容：",
        "no_issues": "  なし",
        "severity_error": "エラー",
        "severity_warning": "警告",
        "severity_info": "情報",
    },
}


FINDING_TEXT = {
    "zh_cn": {
        "save_size": "存档大小异常（实际 / 期望）：{values}",
        "checksum": "当前内存数据的校验和不匹配；如有未保存编辑，这是预期现象",
        "difficulty": "难度值无法识别：{values}",
        "item_unknown": "未知物品 ID：{values}",
        "item_duplicate": "重复物品 ID：{values}",
        "item_quantity": "物品数量超过编辑器安全范围 99：{values}",
        "item_orphan": "空物品槽带有非零数量：{values}",
        "team_unknown": "队伍槽含未知角色 ID：{values}",
        "team_duplicate": "队伍中存在重复角色：{values}",
        "appearance_unknown": "外观槽含未知模型 ID：{values}",
        "recipe_mirror": "三份料理手册位图不一致：{values}",
        "monster_unknown": "未知怪物代码：{values}",
        "monster_duplicate": "重复怪物记录：{values}",
        "monster_partial": "存在部分资料记录；未知子位保持只读：{values}",
        "monster_missing": "尚未登记的怪物代码：{values}",
        "monster_orphan": "空怪物槽带有非零状态数据：{values}",
        "reference_missing": "参考数据缺失或为空：{values}",
        "reference_edition": "参考数据目标版本不是 nisa_pc：{values}",
    },
    "en": {
        "save_size": "Unexpected save size (actual / expected): {values}",
        "checksum": "The in-memory checksum does not match; this is expected after unsaved edits",
        "difficulty": "Unknown difficulty value: {values}",
        "item_unknown": "Unknown item IDs: {values}",
        "item_duplicate": "Duplicate item IDs: {values}",
        "item_quantity": "Item quantities exceed the editor-safe limit of 99: {values}",
        "item_orphan": "Empty item slots contain nonzero quantities: {values}",
        "team_unknown": "Party slots contain unknown character IDs: {values}",
        "team_duplicate": "Duplicate party characters: {values}",
        "appearance_unknown": "Appearance slots contain unknown model IDs: {values}",
        "recipe_mirror": "The three recipe-book bitmaps differ: {values}",
        "monster_unknown": "Unknown monster codes: {values}",
        "monster_duplicate": "Duplicate monster records: {values}",
        "monster_partial": "Partial monster records found; unknown sub-bits remain read-only: {values}",
        "monster_missing": "Monster codes not yet registered: {values}",
        "monster_orphan": "Empty monster slots contain nonzero state bytes: {values}",
        "reference_missing": "Reference data is missing or empty: {values}",
        "reference_edition": "Reference target edition is not nisa_pc: {values}",
    },
    "ja": {
        "save_size": "セーブサイズが不正です（実際 / 期待値）：{values}",
        "checksum": "メモリ上のチェックサムが不一致です。未保存の編集後は正常な状態です",
        "difficulty": "不明な難易度：{values}",
        "item_unknown": "不明なアイテム ID：{values}",
        "item_duplicate": "重複アイテム ID：{values}",
        "item_quantity": "アイテム数が安全上限 99 を超えています：{values}",
        "item_orphan": "空アイテムスロットに数量があります：{values}",
        "team_unknown": "パーティ枠に不明なキャラ ID があります：{values}",
        "team_duplicate": "パーティ内に重複キャラがあります：{values}",
        "appearance_unknown": "外見枠に不明なモデル ID があります：{values}",
        "recipe_mirror": "3 つの料理手帳ビットマップが一致しません：{values}",
        "monster_unknown": "不明な魔獣コード：{values}",
        "monster_duplicate": "魔獣レコードが重複しています：{values}",
        "monster_partial": "部分データがあります。不明なサブビットは読み取り専用です：{values}",
        "monster_missing": "未登録の魔獣コード：{values}",
        "monster_orphan": "空の魔獣枠に状態データがあります：{values}",
        "reference_missing": "参照データが見つからないか空です：{values}",
        "reference_edition": "参照データの対象版が nisa_pc ではありません：{values}",
    },
}


def _locale(locale):
    return locale if locale in TEXT else "zh_cn"


def _preview(values, formatter=str, limit=12):
    rows = [formatter(value) for value in values]
    if len(rows) > limit:
        return ", ".join(rows[:limit]) + f" … (+{len(rows) - limit})"
    return ", ".join(rows)


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    code: str
    values: str = ""

    def render(self, locale="zh_cn"):
        locale = _locale(locale)
        template = FINDING_TEXT[locale][self.code]
        return template.format(values=self.values)


@dataclass(frozen=True)
class SaveAuditReport:
    metrics: dict
    findings: tuple[AuditFinding, ...]

    @property
    def severity_counts(self):
        counts = Counter(finding.severity for finding in self.findings)
        return {key: counts.get(key, 0) for key in ("error", "warning", "info")}

    @property
    def is_clean(self):
        return not any(finding.severity in {"error", "warning"} for finding in self.findings)

    def render(self, locale="zh_cn"):
        locale = _locale(locale)
        text = TEXT[locale]
        counts = self.severity_counts
        overall_key = "overall_clean" if self.is_clean else "overall_issues"
        checksum = self.metrics.get("checksum_valid")
        checksum_text = text["unknown"] if checksum is None else text["valid" if checksum else "invalid"]
        lines = [
            text["title"],
            text[overall_key].format(errors=counts["error"], warnings=counts["warning"], infos=counts["info"]),
            "",
            text["size"].format(size=self.metrics["save_size"], checksum=checksum_text),
            text["items"].format(**self.metrics["items"]),
            text["monsters"].format(**self.metrics["monsters"]),
            text["references"].format(**self.metrics["references"]),
            "",
            text["issues"],
        ]
        if not self.findings:
            lines.append(text["no_issues"])
        else:
            for finding in self.findings:
                severity = text[f"severity_{finding.severity}"]
                lines.append(f"  [{severity}] {finding.render(locale)}")
        return "\n".join(lines)


class SaveAuditor:
    """Deep read-only module: one audit call hides all verified layout checks."""

    def __init__(self, known_item_codes=(), known_monster_codes=(), reference_edition="unknown"):
        self.known_item_codes = frozenset(int(code) for code in known_item_codes)
        self.known_monster_codes = tuple(int(code) for code in known_monster_codes)
        self.known_monster_set = frozenset(self.known_monster_codes)
        self.reference_edition = str(reference_edition or "unknown")

    def audit(self, data, checksum_valid=None):
        raw = bytes(data or b"")
        findings = []
        metrics = {
            "save_size": len(raw),
            "checksum_valid": checksum_valid,
            "items": {"populated": 0, "capacity": ((ITEMS_END - ITEMS_START) // 4) + 1, "unique": 0},
            "monsters": {
                "known": 0, "total": len(self.known_monster_codes), "complete": 0,
                "partial": 0, "missing": len(self.known_monster_codes),
            },
            "references": {
                "items": len(self.known_item_codes), "monsters": len(self.known_monster_codes),
                "edition": self.reference_edition,
            },
        }
        if len(raw) != EXPECTED_SIZE:
            findings.append(AuditFinding("error", "save_size", f"{len(raw)} / {EXPECTED_SIZE}"))
            return SaveAuditReport(metrics, tuple(findings))
        if checksum_valid is False:
            findings.append(AuditFinding("warning", "checksum"))
        if not self.known_item_codes:
            findings.append(AuditFinding("error", "reference_missing", "items"))
        if not self.known_monster_codes:
            findings.append(AuditFinding("error", "reference_missing", "monsters"))
        if self.reference_edition not in {"nisa_pc", "unknown"}:
            findings.append(AuditFinding("error", "reference_edition", self.reference_edition))

        difficulty = raw[DIFFICULTY_OFFSET]
        if difficulty not in range(4):
            findings.append(AuditFinding("error", "difficulty", str(difficulty)))

        item_entries = []
        orphan_item_slots = []
        for slot, pos in enumerate(range(ITEMS_START, ITEMS_END + 1, 4)):
            code, quantity = struct.unpack_from("<HH", raw, pos)
            if code:
                item_entries.append((slot, code, quantity))
            elif quantity:
                orphan_item_slots.append(f"#{slot}={quantity}")
        item_counts = Counter(code for _slot, code, _quantity in item_entries)
        metrics["items"].update(populated=len(item_entries), unique=len(item_counts))
        unknown_items = sorted(code for code in item_counts if code not in self.known_item_codes)
        duplicate_items = sorted(code for code, count in item_counts.items() if count > 1)
        excessive_items = sorted((code, quantity) for _slot, code, quantity in item_entries if quantity > 99)
        if unknown_items:
            findings.append(AuditFinding("warning", "item_unknown", _preview(unknown_items, lambda x: f"0x{x:04X}")))
        if duplicate_items:
            findings.append(AuditFinding("warning", "item_duplicate", _preview(duplicate_items, lambda x: f"0x{x:04X}")))
        if excessive_items:
            findings.append(AuditFinding("warning", "item_quantity", _preview(excessive_items, lambda x: f"0x{x[0]:04X}={x[1]}")))
        if orphan_item_slots:
            findings.append(AuditFinding("warning", "item_orphan", _preview(orphan_item_slots)))

        team = [struct.unpack_from("<H", raw, offset)[0] for offset in TEAM_SLOTS]
        unknown_team = [(index + 1, value) for index, value in enumerate(team) if value not in KNOWN_TEAM_IDS]
        team_counts = Counter(value for value in team if value not in {0xFF, 0xFFFF})
        duplicate_team = sorted(value for value, count in team_counts.items() if count > 1)
        if unknown_team:
            findings.append(AuditFinding("error", "team_unknown", _preview(unknown_team, lambda x: f"#{x[0]}={x[1]}")))
        if duplicate_team:
            findings.append(AuditFinding("warning", "team_duplicate", _preview(duplicate_team)))

        appearance = [struct.unpack_from("<H", raw, offset)[0] for offset in ROLE_DISPLAY_OFFSETS]
        unknown_appearance = [(index + 1, value) for index, value in enumerate(appearance) if value not in KNOWN_ROLE_DISPLAY_IDS]
        if unknown_appearance:
            findings.append(AuditFinding("error", "appearance_unknown", _preview(unknown_appearance, lambda x: f"#{x[0]}={x[1]}")))

        recipe_masks = [struct.unpack_from("<I", raw, offset)[0] & RECIPE_BOOK_MASK for offset in RECIPE_BOOK_OFFSETS]
        if len(set(recipe_masks)) > 1:
            findings.append(AuditFinding("warning", "recipe_mirror", _preview(recipe_masks, lambda x: f"0x{x:08X}")))

        monster_rows = []
        orphan_monster_slots = []
        for slot, pos in enumerate(range(MONSTER_START, MONSTER_END + 1, MONSTER_RECORD_SIZE)):
            code, flag, resistance, stats, get_item = struct.unpack_from("<I4B", raw, pos)
            payload = bytes((flag, resistance, stats, get_item))
            if code:
                monster_rows.append((slot, code, payload))
            elif payload != b"\0\0\0\0":
                orphan_monster_slots.append(f"#{slot}=0x{payload.hex().upper()}")
        monster_counts = Counter(code for _slot, code, _payload in monster_rows)
        present_known = self.known_monster_set & set(monster_counts)
        complete = {
            code for _slot, code, payload in monster_rows
            if code in self.known_monster_set and payload == MONSTER_COMPLETE_PAYLOAD
        }
        partial = present_known - complete
        missing = self.known_monster_set - present_known
        metrics["monsters"].update(
            known=len(present_known), complete=len(complete), partial=len(partial),
            missing=len(missing),
        )
        unknown_monsters = sorted(code for code in monster_counts if code not in self.known_monster_set)
        duplicate_monsters = sorted(code for code, count in monster_counts.items() if count > 1)
        if unknown_monsters:
            findings.append(AuditFinding("warning", "monster_unknown", _preview(unknown_monsters, lambda x: f"0x{x:08X}")))
        if duplicate_monsters:
            findings.append(AuditFinding("warning", "monster_duplicate", _preview(duplicate_monsters, lambda x: f"0x{x:08X}")))
        if partial:
            findings.append(AuditFinding("info", "monster_partial", _preview(sorted(partial), lambda x: f"0x{x:08X}")))
        if missing:
            findings.append(AuditFinding("info", "monster_missing", _preview(sorted(missing), lambda x: f"0x{x:08X}")))
        if orphan_monster_slots:
            findings.append(AuditFinding("warning", "monster_orphan", _preview(orphan_monster_slots)))
        return SaveAuditReport(metrics, tuple(findings))


def load_default_save_auditor(root=None):
    from ao_items_db import ITEM_DB
    from ao_monsters_db import load_default_monster_catalog

    catalog = load_default_monster_catalog(root)
    edition = catalog.metadata.get("target_save_edition", "unknown")
    return SaveAuditor(ITEM_DB, (record.save_code for record in catalog.records()), edition)
