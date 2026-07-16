from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import re
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = ROOT / 'ao_zh_glossary.json'
OUT_MD = ROOT / 'ao_zh_glossary.md'
ITEM_I18N_JSON = ROOT / 'ao_item_i18n.json'
ACHIEVEMENT_I18N_JSON = ROOT / 'ao_achievement_i18n.json'
MAGIC_I18N_JSON = ROOT / 'ao_magic_i18n.json'

CATEGORY_ZH = {
    'book': '书籍/手册',
    'fishing_rod': '钓具-钓竿',
    'fishing_bait': '钓具-鱼饵',
    'fishing_fish': '鱼类',
    'food': '食材',
    'props_normal': '道具-普通',
    'props_cooking': '料理',
    'equipment_weapon_generic': '装备-武器-通用',
    'equipment_weapon_Lloyd': '装备-武器-罗伊德',
    'equipment_weapon_Elie': '装备-武器-艾莉',
    'equipment_weapon_Tio': '装备-武器-缇欧',
    'equipment_weapon_Randy': '装备-武器-兰迪',
    'equipment_weapon_Lazy': '装备-武器-瓦吉',
    'equipment_weapon_Noel': '装备-武器-诺艾尔',
    'equipment_weapon_Rixia': '装备-武器-莉夏',
    'equipment_weapon_Dudley': '装备-武器-达德利',
    'equipment_weapon_Arios': '装备-武器-亚里欧斯',
    'equipment_weapon_Zeit': '装备-武器-蔡特',
    'equipment_clothes': '装备-服装',
    'equipment_shoes': '装备-鞋子',
    'equipment_jewelry': '装备-饰品',
    'circuit_normal': '回路-普通',
    'circuit_core': '回路-核心',
    'circuit_debug': '回路-Debug/未确认',
    'event_story': '事件-剧情',
    'event_furnishing': '事件-家具',
    'event_car': '事件-导力车',
}

CHAR_ZH = {
    'Lloyd': '罗伊德', 'Elie': '艾莉', 'Tio': '缇欧', 'Randy': '兰迪',
    'Wazy': '瓦吉', 'Rixia': '莉夏', 'Zeit': '蔡特', 'Arios': '亚里欧斯',
    'Noel': '诺艾尔', 'Dudley': '达德利', 'Garcia': '加尔西亚',
}

S_BREAK_SAVE_IDS = [
    ('Lloyd', 0x0118, '猛虎冲锋'), ('Lloyd', 0x0119, '升龙旭日'), ('Lloyd', 0x011A, '陨星粉碎'),
    ('Lloyd', 0x011B, '猛虎冲锋II'), ('Lloyd', 0x011C, '升龙旭日II'),
    ('Elie', 0x011D, '极光之雨'), ('Elie', 0x011E, '大气能量炮'), ('Elie', 0x011F, '神圣十字波'),
    ('Elie', 0x0120, '极光之雨II'), ('Elie', 0x0121, '大气能量炮II'),
    ('Tio', 0x0122, '以太爆裂射'), ('Tio', 0x0123, '虚无领域'), ('Tio', 0x0124, '星灵装甲'),
    ('Tio', 0x0125, '以太爆裂射II'),
    ('Randy', 0x0127, '赤炎飓风'), ('Randy', 0x0128, '死亡天蝎'), ('Randy', 0x0129, '狂战士'),
    ('Randy', 0x012A, '赤炎飓风II'), ('Randy', 0x012B, '死亡天蝎II'),
    ('Wazy', 0x012C, '致命天堂'), ('Wazy', 0x012D, '空虚手臂'), ('Wazy', 0x012F, '致命天堂II'),
    ('Rixia', 0x0131, '幻月之舞'), ('Rixia', 0x0134, '真·幻月之舞'),
    ('Arios', 0x013B, '风神裂波'), ('Arios', 0x013C, '终之太刀-黑皇-'),
    ('Noel', 0x0140, '暴击风暴'), ('Noel', 0x0141, '武装军势'), ('Noel', 0x0143, '暴击风暴II'),
    ('Dudley', 0x0145, '正义之拳'), ('Dudley', 0x0146, '正义制裁'), ('Dudley', 0x0148, '正义之拳II'),
    ('Garcia', 0x014A, '杀戮驱驰'),
]

ACHIEVEMENT_JA = {
    '三星厨师': '三ツ星シェフ',
    '爆钓王': '爆釣王',
    '宝箱猎人': 'トレジャーハンター',
    '小说爱好者': 'ノベルラバー',
    '回路收藏家': 'クオーツコレクター',
    '炎之料理人': '炎の料理人',
    '天眼的智者': '天眼の識者',
    '市民的英雄': '市民のヒーロー',
    '千战之志士': '千討の志士',
    '历战之胜者': '歴戦の勝者',
    '奋战之猛士': '奮戦の猛者',
    '力战之勇士': '力戦の勇士',
    '百万富翁': '百万長者',
    '组合技大师': 'コンビマスター',
    'D之追及者': 'Dの追及者',
    '不拘一格的厨师': '型破りシェフ',
    '导力车发烧友': 'カーマニア',
    '家具收藏家': 'インテリアコレクター',
    '无双之猎士': '無双の烈士',
    '最强之剑': '至高の剣',
    '超一流搜查官': '超一流捜査官',
    '持续的压迫': '継続の粋人',
    '超绝秘技': '超絶秘技',
    '雷光一闪': '雷光一閃',
    '短暂的休息': '束の間の休息',
    '西塞姆利亚通商会议': '西ゼムリア通商会議',
    'D之残影': 'Dの残影',
    '传说的搜查官': '伝説の捜査官',
    '干练的搜查官': '腕利き捜査官',
    '艾尼格玛Ⅱ用户': 'エニグマⅡユーザー',
    '至境之珠': '至境の珠',
    '与莉夏的羁绊': 'リーシャとの絆',
    '与瓦吉的羁绊': 'ワジとの絆',
    '与诺艾尔的羁绊': 'ノエルとの絆',
    '与达德利的羁绊': 'ダドリーとの絆',
    '即便如此我们也…': 'それでも僕らは。',
    '跨越虚幻的乐园': '偽りの楽土を越えて',
    '命运未卜的克洛斯贝尔': '運命のクロスベル',
    '胎动～众兽的狂欢节': '胎動～獣たちの謝肉祭',
    '连战连胜': '連戦連破',
    '绚烂攻击': '絢爛攻守',
    '百花迎击': '百花迎撃',
    '刚之追随者': '鋼に届きし者',
    '红之讨伐者': '紅の討伐者',
    '与兰迪的羁绊': 'ランディとの絆',
    '与缇欧的羁绊': 'ティオとの絆',
    '与艾莉的羁绊': 'エリィとの絆',
    '绮耀之贤士': '七耀の賢士',
    '怪物射击大师': 'ホラーバスター',
    '波波碰大师': 'ポムっと！マスター',
    '传承的思念～不断的羁绊': '届いた想い、繋がる絆',
    '解明真相者': '解き明かせし者',
    '爆裂果敢': '爆裂果敢',
    '赶紧杀绝': '滅絶淘汰',
    '霸头歼灭': '八頭撃滅',
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def clean_skill_category(cat):
    if cat == '⑨м':
        return 'S技'
    return cat or '未分类'


def split_jp_zh(name):
    if not name:
        return None, None
    s = str(name).strip()
    parts = re.split(r'\s+', s, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, s


def hex4(n):
    return f'0x{n:04X}'


def md_cell(value):
    if value is None:
        return ''
    text = str(value)
    text = text.replace(chr(92), chr(92) + chr(92))
    text = text.replace('|', chr(92) + '|')
    text = text.replace('\r\n', '<br>')
    text = text.replace('\n', '<br>')
    return text

def main():
    items_mod = load_module('ao_items_db_for_glossary', ROOT / 'ao_items_db.py')
    editor_mod = load_module('ao_save_editor_for_glossary', ROOT / 'ao_save_editor.py')
    ref = json.loads((ROOT / 'ao_reference_data.json').read_text(encoding='utf-8'))
    item_i18n = {}
    if ITEM_I18N_JSON.exists():
        item_i18n_data = json.loads(ITEM_I18N_JSON.read_text(encoding='utf-8'))
        item_i18n = {int(row['id_dec']): row for row in item_i18n_data.get('items', [])}
    achievement_i18n = {}
    if ACHIEVEMENT_I18N_JSON.exists():
        achievement_i18n_data = json.loads(ACHIEVEMENT_I18N_JSON.read_text(encoding='utf-8'))
        achievement_i18n = {
            (int(row['bitmap_part']), int(row['bit'])): row
            for row in achievement_i18n_data.get('achievements', [])
        }
    magic_i18n = []
    if MAGIC_I18N_JSON.exists():
        magic_i18n_data = json.loads(MAGIC_I18N_JSON.read_text(encoding='utf-8'))
        magic_i18n = magic_i18n_data.get('magic', [])

    items = []
    for code, (cat, name) in sorted(items_mod.ITEM_DB.items()):
        i18n = item_i18n.get(code, {})
        items.append({
            'id_hex': hex4(code),
            'id_dec': code,
            'category': cat,
            'category_zh': CATEGORY_ZH.get(cat, cat),
            'zh_cn': name,
            'en': i18n.get('en'),
            'en_desc': i18n.get('en_desc'),
            'ja': i18n.get('ja'),
            'ja_desc': i18n.get('ja_desc'),
            'id_status': 'save_item_id',
            'source': 'ao_items_db.py / BZH item definitions' + (' + items.json' if i18n else ''),
        })

    role_display = []
    for code, name in sorted(editor_mod.ROLE_DISPLAY_NAMES.items()):
        role_display.append({
            'id_dec': code,
            'id_hex': hex4(code),
            'zh_cn': name,
            'id_status': 'save_role_display_id',
            'source': 'ao_save_editor.py ROLE_DISPLAY_NAMES',
        })

    characters = []
    for en, base in editor_mod.CHAR_BASES.items():
        characters.append({
            'key': en,
            'zh_cn': CHAR_ZH.get(en, en),
            'base_offset_hex': f'0x{base:08X}',
            'id_status': 'character_save_block_base',
            'source': 'ao_save_editor.py CHAR_BASES',
        })

    likeability = []
    for name, off in editor_mod.LIKEABILITY.items():
        likeability.append({
            'offset_hex': f'0x{off:08X}',
            'zh_cn': name,
            'id_status': 'save_likeability_offset',
            'source': 'ao_save_editor.py LIKEABILITY',
        })

    battle_stats = []
    for name, off in editor_mod.BATTLE_STATS.items():
        battle_stats.append({
            'offset_hex': f'0x{off:08X}',
            'zh_cn': name,
            'id_status': 'save_battle_stat_offset',
            'source': 'ao_save_editor.py BATTLE_STATS',
        })

    achievements = []
    for part, bit, name in editor_mod.ACHIEVEMENT_NAMES:
        i18n = achievement_i18n.get((part, bit), {})
        achievements.append({
            'bitmap_part': part,
            'bit': bit,
            'zh_cn': name,
            'en': i18n.get('en'),
            'en_desc': i18n.get('en_desc'),
            'ja': i18n.get('ja') or ACHIEVEMENT_JA.get(name),
            'ja_desc': i18n.get('ja_desc'),
            'game_achievement_id': i18n.get('game_achievement_id'),
            'ja_status': 'matched_by_supplied_json' if i18n.get('ja') else ('matched_by_zh_name' if name in ACHIEVEMENT_JA else 'needs_review'),
            'id_status': 'save_achievement_bitmap_bit',
            'source': 'ao_save_editor.py ACHIEVEMENT_NAMES + supplied achievement JSON',
        })

    s_breaks = []
    for owner, code, name in S_BREAK_SAVE_IDS:
        s_breaks.append({
            'id_hex': hex4(code),
            'id_dec': code,
            'owner_key': owner,
            'owner_zh': CHAR_ZH.get(owner, owner),
            'zh_cn': name,
            'skill_kind': 'S技',
            'id_status': 'confirmed_save_skill_id',
            'source': 'BZH bzh_ank_se_code_define_skill.h + text_define_skill.h',
        })

    ref_skills = []
    for rec in ref['skill_data']['records']:
        full_name = rec.get('技能名称(名称翻译待逐渐修正)')
        jp, zh = split_jp_zh(full_name)
        if not zh:
            continue
        ref_skills.append({
            'reference_no': rec.get('编号'),
            'reference_row': rec.get('row'),
            'reference_code_first_word_hex': hex4(rec['技能代码首word_le']) if rec.get('技能代码首word_le') is not None else None,
            'skill_kind': clean_skill_category(rec.get('技能类别')),
            'caster': rec.get('技能施放单位'),
            'zh_cn': zh,
            'jp_name': jp,
            'effect_zh': rec.get('技能效果'),
            'cost': rec.get('CP/EP'),
            'id_status': 'reference_table_id_not_save_slot_id',
            'source': '碧轨魔法战技数据表0.099_201506142001.xlsx',
        })

    level_formulas = []
    for rec in ref['level_formula_data']['azure']['records']:
        level_formulas.append({
            'zh_cn': rec.get('角色名'),
            'hp_formula': rec.get('HP最大值'),
            'ep_initial': rec.get('EP初始'),
            'str_formula': rec.get('STR'),
            'def_formula': rec.get('DEF'),
            'ats_formula': rec.get('ATS'),
            'adf_formula': rec.get('ADF'),
            'spd_formula': rec.get('SPD'),
            'mov': rec.get('MOV'),
            'rng_initial_weapon': rec.get('RNG(初始武器)'),
            'dex_formula': rec.get('DEX'),
            'agl_formula': rec.get('AGL'),
            'id_status': 'level_formula_reference_no_exp_table',
            'source': '零之轨迹&碧之轨迹 人物属性值与等级函数关系表Final20120629.xls',
        })

    data = {
        'meta': {
            'title': 'Ao no Kiseki / Trails to Azure 中文术语表',
            'language': 'zh_cn',
            'notes': [
                '物品 id_hex 是存档物品 ID；中文名按 ID 采用 Ouroboros/Falcom ItemNameMap.py。' + (' 英文/日文名来自用户提供的 item JSON，可直接匹配的条目：' + str(len(item_i18n)) + '。' if item_i18n else ''),
                'S 技 id_hex 是 BZH 已确认的存档技能 ID。',
                'reference_skills 中的 reference_no / reference_code_first_word_hex 来自参考表，不等同于存档战技槽位 ID。',
                '等级函数表只提供属性公式，不提供 EXP 阈值表。',
            ],
        },
        'items': items,
        's_break_save_ids': s_breaks,
        'reference_skills': ref_skills,
        'role_display': role_display,
        'characters': characters,
        'likeability': likeability,
        'battle_stats': battle_stats,
        'achievements': achievements,
        'magic_i18n': magic_i18n,
        'level_formulas': level_formulas,
    }
    OUT_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    by_cat = defaultdict(list)
    for item in items:
        by_cat[item['category_zh']].append(item)
    by_skill_kind = defaultdict(list)
    for skill in ref_skills:
        by_skill_kind[skill['skill_kind']].append(skill)

    lines = []
    lines.append('# Ao no Kiseki / Trails to Azure 中文术语表')
    lines.append('')
    lines.append('> 本表整理当前编辑器和参考资料中的中文名称与 ID。`reference_skills` 的编号来自参考表，不等同于存档战技槽位 ID。')
    lines.append('')
    lines.append('## 统计')
    lines.append('')
    lines.append(f'- 物品/装备/回路等存档物品 ID：{len(items)}')
    lines.append(f'- 已确认 S 技存档 ID：{len(s_breaks)}')
    lines.append(f'- 参考技能/魔法条目：{len(ref_skills)}')
    lines.append(f'- Magic CSV 本地化条目：{len(magic_i18n)}')
    lines.append(f'- 角色外观 ID：{len(role_display)}')
    lines.append(f'- 成就位：{len(achievements)}')
    lines.append('')

    lines.append('## 已确认 S 技存档 ID')
    lines.append('')
    lines.append('| ID | 角色 | 中文名 |')
    lines.append('|---|---|---|')
    for row in s_breaks:
        lines.append(f"| {row['id_hex']} | {row['owner_zh']} | {row['zh_cn']} |")
    lines.append('')

    lines.append('## 角色外观 ID')
    lines.append('')
    lines.append('| ID | 中文名 |')
    lines.append('|---|---|')
    for row in role_display:
        lines.append(f"| {row['id_dec']} / {row['id_hex']} | {row['zh_cn']} |")
    lines.append('')

    lines.append('## 存档物品 ID')
    for cat in sorted(by_cat):
        rows = by_cat[cat]
        lines.append('')
        lines.append(f'### {cat} ({len(rows)})')
        lines.append('')
        lines.append('| ID | 中文名 | 英文名 | 日文名 | 原类别 |')
        lines.append('|---|---|---|---|---|')
        for row in rows:
            lines.append(f"| {row['id_hex']} | {row['zh_cn']} | {row.get('en') or ''} | {row.get('ja') or ''} | {row['category']} |")
    lines.append('')

    lines.append('## 参考技能/魔法术语')
    for kind in sorted(by_skill_kind):
        rows = by_skill_kind[kind]
        lines.append('')
        lines.append(f'### {kind} ({len(rows)})')
        lines.append('')
        lines.append('| 参考编号 | 参考代码首 word | 中文名 | 日文名 | 施放单位 | 效果 |')
        lines.append('|---|---|---|---|---|---|')
        for row in rows:
            lines.append(f"| {row.get('reference_no') or ''} | {row.get('reference_code_first_word_hex') or ''} | {row.get('zh_cn') or ''} | {row.get('jp_name') or ''} | {row.get('caster') or ''} | {row.get('effect_zh') or ''} |")
    lines.append('')

    lines.append('## 成就位')
    lines.append('')
    lines.append('| Part | Bit | 游戏成就ID | 中文名 | 英文名 | 日文名 | 英文描述 | 日文描述 |')
    lines.append('|---|---|---|---|---|---|---|---|')
    for row in achievements:
        lines.append(f"| {row['bitmap_part']} | {row['bit']} | {row.get('game_achievement_id') or ''} | {md_cell(row['zh_cn'])} | {md_cell(row.get('en'))} | {md_cell(row.get('ja'))} | {md_cell(row.get('en_desc'))} | {md_cell(row.get('ja_desc'))} |")
    lines.append('')

    lines.append('## Magic CSV 本地化参考')
    lines.append('')
    lines.append('> `reference_no_guess` 是 CSV 的 1-based 行号；当前不把它声明为存档战技槽位 ID。日文列来自用户提供 CSV 的原始文本，存在 mojibake，需后续复核。')
    lines.append('')
    lines.append('| CSV行 | Battle Entry | 英文名 | 英文描述 | 日文原始列 |')
    lines.append('|---|---|---|---|---|')
    for row in magic_i18n:
        lines.append(f"| {row.get('csv_row') or ''} | {row.get('battle_entry_id') or ''} | {md_cell(row.get('en'))} | {md_cell(row.get('en_desc'))} | {md_cell(row.get('ja_raw'))} |")
    lines.append('')

    lines.append('## 等级属性公式')
    lines.append('')
    lines.append('| 角色 | HP | STR | DEF | ATS | ADF | SPD | DEX | AGL |')
    lines.append('|---|---|---|---|---|---|---|---|---|')
    for row in level_formulas:
        lines.append(f"| {row['zh_cn']} | {row['hp_formula']} | {row['str_formula']} | {row['def_formula']} | {row['ats_formula']} | {row['adf_formula']} | {row['spd_formula']} | {row['dex_formula']} | {row['agl_formula']} |")

    OUT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(OUT_JSON)
    print(OUT_MD)
    print(json.dumps({
        'items': len(items),
        's_break_save_ids': len(s_breaks),
        'reference_skills': len(ref_skills),
        'role_display': len(role_display),
        'achievements': len(achievements),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
