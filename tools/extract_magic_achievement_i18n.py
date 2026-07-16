from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS = Path.home() / "Downloads"

MAGIC_JP_CSV = DOWNLOADS / "magic_jp.csv"
MAGIC_US_CSV = DOWNLOADS / "magic_us.csv"
ACH_JA_JSON = DOWNLOADS / "achievements_ja.json"
ACH_US_JSON = DOWNLOADS / "achievements_us.json"

OUT_MAGIC = ROOT / "ao_magic_i18n.json"
OUT_ACH = ROOT / "ao_achievement_i18n.json"


ACH_ZH_TO_JA = {
    "三星厨师": "三ツ星シェフ",
    "爆钓王": "爆釣王",
    "宝箱猎人": "トレジャーハンター",
    "小说爱好者": "ノベルラバー",
    "回路收藏家": "クオーツコレクター",
    "炎之料理人": "炎の料理人",
    "天眼的智者": "天眼の識者",
    "市民的英雄": "市民のヒーロー",
    "千战之志士": "千討の志士",
    "历战之胜者": "歴戦の勝者",
    "奋战之猛士": "奮戦の猛者",
    "力战之勇士": "力戦の勇士",
    "百万富翁": "百万長者",
    "组合技大师": "コンビマスター",
    "D之追及者": "Ｄの追及者",
    "不拘一格的厨师": "型破りシェフ",
    "导力车发烧友": "カーマニア",
    "家具收藏家": "インテリアコレクター",
    "无双之猎士": "無双の烈士",
    "最强之剑": "至高の剣",
    "超一流搜查官": "超一流捜査官",
    "持续的压迫": "継続の粋人",
    "超绝秘技": "超絶秘技",
    "雷光一闪": "雷光一閃",
    "短暂的休息": "束の間の休息",
    "西塞姆利亚通商会议": "西ゼムリア通商会議",
    "预兆~新的生活": "予兆～新たなる日々",
    "D之残影": "Ｄの残影",
    "传说的搜查官": "伝説の捜査官",
    "干练的搜查官": "腕利き捜査官",
    "艾尼格玛Ⅱ用户": "エニグマⅡユーザー",
    "至境之珠": "至境の珠",
    "与莉夏的羁绊": "リーシャとの絆",
    "与瓦吉的羁绊": "ワジとの絆",
    "与诺艾尔的羁绊": "ノエルとの絆",
    "与达德利的羁绊": "ダドリーとの絆",
    "即便如此我们也…": "それでも僕らは。",
    "跨越虚幻的乐园": "偽りの楽土を越えて",
    "命运未卜的克洛斯贝尔": "運命のクロスベル",
    "胎动～众兽的狂欢节": "胎動～獣たちの謝肉祭",
    "连战连胜": "連戦連破",
    "绚烂攻击": "絢爛攻守",
    "百花迎击": "百花迎撃",
    "刚之追随者": "鋼に届きし者",
    "红之讨伐者": "紅の討伐者",
    "与兰迪的羁绊": "ランディとの絆",
    "与缇欧的羁绊": "ティオとの絆",
    "与艾莉的羁绊": "エリィとの絆",
    "绮耀之贤士": "七耀の賢士",
    "怪物射击大师": "ホラーバスター",
    "波波碰大师": "ポムっと！マスター",
    "传承的思念～不断的羁绊": "届いた想い、繋がる絆",
    "解明真相者": "解き明かせし者",
    "爆裂果敢": "爆裂果敢",
    "赶紧杀绝": "滅絶淘汰",
    "霸头歼灭": "八頭撃滅",
}


def read_json_auto(path: Path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp932", "gb18030"):
        try:
            return json.loads(raw.decode(enc))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise UnicodeError(f"unable to decode {path}")


def read_magic_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


def build_magic_i18n():
    jp_rows = read_magic_csv(MAGIC_JP_CSV)
    us_rows = read_magic_csv(MAGIC_US_CSV)
    rows = []
    for idx, (jp, us) in enumerate(zip(jp_rows, us_rows), start=1):
        en = us[19].strip() if len(us) > 19 else ""
        ja_raw = jp[19].strip() if len(jp) > 19 else ""
        if not en and not ja_raw:
            continue
        rows.append(
            {
                "csv_row": idx,
                "reference_no_guess": idx,
                "battle_entry_id": int(us[7]) if len(us) > 7 and us[7].isdigit() else None,
                "en": en,
                "en_desc": us[20].strip() if len(us) > 20 else "",
                "ja_raw": ja_raw,
                "ja_status": "raw_csv_needs_review",
                "ja_desc_raw": jp[20].strip() if len(jp) > 20 else "",
                "source": "magic_us.csv / magic_jp.csv",
            }
        )
    OUT_MAGIC.write_text(
        json.dumps(
            {
                "meta": {
                    "source": "User supplied magic_us.csv and magic_jp.csv",
                    "notes": [
                        "English names/descriptions are usable as-is.",
                        "Japanese CSV name/description columns are preserved as raw text; some rows appear mojibake-encoded and need review.",
                        "reference_no_guess is the 1-based CSV row and is not a confirmed save skill ID.",
                    ],
                },
                "magic": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return rows


def build_achievement_i18n():
    ja_rows = read_json_auto(ACH_JA_JSON)
    us_rows = read_json_auto(ACH_US_JSON)
    ja_by_name = {row["name"]: row for row in ja_rows if row.get("name")}
    us_by_id = {int(row["id"]): row for row in us_rows if row.get("id") is not None}
    editor = __import__("ao_save_editor")

    achievements = []
    missing = []
    for part, bit, zh in editor.ACHIEVEMENT_NAMES:
        ja_name = ACH_ZH_TO_JA.get(zh)
        ja_row = ja_by_name.get(ja_name or "")
        us_row = us_by_id.get(int(ja_row["id"])) if ja_row else None
        if not ja_row or not us_row:
            missing.append(zh)
        achievements.append(
            {
                "bitmap_part": part,
                "bit": bit,
                "zh_cn": zh,
                "ja": ja_name,
                "ja_desc": ja_row.get("desc") if ja_row else None,
                "en": us_row.get("name") if us_row else None,
                "en_desc": us_row.get("desc") if us_row else None,
                "game_achievement_id": int(ja_row["id"]) if ja_row else None,
                "match_source": "zh_cn_to_ja_name_to_json_id",
            }
        )
    OUT_ACH.write_text(
        json.dumps(
            {
                "meta": {
                    "source": "User supplied achievements_ja.json and achievements_us.json",
                    "missing": missing,
                    "notes": [
                        "bitmap_part/bit are save-editor achievement bitmap locations.",
                        "game_achievement_id is the ID from the supplied achievement JSON and is not the bitmap order.",
                    ],
                },
                "achievements": achievements,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return achievements


def main():
    magic = build_magic_i18n()
    achievements = build_achievement_i18n()
    print(OUT_MAGIC)
    print(OUT_ACH)
    print(json.dumps({"magic": len(magic), "achievements": len(achievements)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
