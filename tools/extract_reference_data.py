from __future__ import annotations

from pathlib import Path
import json
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SKILL_FILE = Path.home() / 'Downloads' / '碧轨魔法战技数据表0.099_201506142001.xlsx'
LEVEL_FILE = Path.home() / 'Downloads' / '零之轨迹&碧之轨迹 人物属性值与等级函数关系表Final20120629.xls'
OUT = ROOT / 'ao_reference_data.json'

TEXT_ALIASES = {
    '︺产': '艾莉',
    '讲疭': '蔡特',
    '脄筽才': '爆雷符',
    'Enigma英格玛': 'ENIGMA II',
    '导力魔法·主回路': '导力魔法·核心回路',
    '主回路': '核心回路',
}


def basic_text(x):
    if pd.isna(x):
        return None
    if not isinstance(x, str):
        if isinstance(x, float) and x.is_integer():
            return int(x)
        return x
    s = x.strip()
    return s or None


def fix_skill_text(x):
    s = basic_text(x)
    if not isinstance(s, str):
        return s
    # Skill workbook text is mojibake: intended GBK/CP936 decoded as Big5/CP950.
    try:
        repaired = s.encode('cp950').decode('cp936').strip()
    except Exception:
        repaired = s
    for bad, good in TEXT_ALIASES.items():
        repaired = repaired.replace(bad, good)
    return repaired


def norm_header(x, fallback):
    s = basic_text(x)
    if s is None:
        return fallback
    return str(s).replace('\n', ' ').strip()


def parse_hex_bytes(s):
    if not isinstance(s, str):
        return []
    return [int(part, 16) for part in re.findall(r'[0-9A-Fa-f]{2}', s)]


def read_azure_skill_table():
    df = pd.read_excel(SKILL_FILE, sheet_name='碧之轨迹魔法战技详细数据表', header=None)
    headers = [norm_header(df.iat[0, i], f'col_{i}') for i in range(df.shape[1])]
    detail_headers = [norm_header(df.iat[1, i], f'detail_{i}') for i in range(df.shape[1])]
    records = []
    for r in range(2, df.shape[0]):
        row = df.iloc[r]
        if row.isna().all():
            continue
        rec = {'row': r + 1}
        for c in range(df.shape[1]):
            key = headers[c]
            if key.startswith('col_') and detail_headers[c] and not str(detail_headers[c]).startswith('detail_'):
                key = f'detail_{detail_headers[c]}'
            rec[key] = fix_skill_text(row.iat[c])
        code_text = rec.get('技能代码')
        code_bytes = parse_hex_bytes(code_text)
        rec['技能代码_bytes'] = code_bytes
        if len(code_bytes) >= 2:
            rec['技能代码首word_le'] = code_bytes[0] | (code_bytes[1] << 8)
        records.append(rec)
    return {
        'file': str(SKILL_FILE),
        'sheet': '碧之轨迹魔法战技详细数据表',
        'shape': list(df.shape),
        'columns': headers,
        'detail_columns': detail_headers,
        'records': records,
    }


def read_level_formula_table(sheet_name):
    df = pd.read_excel(LEVEL_FILE, sheet_name=sheet_name, header=None)
    base_defs = basic_text(df.iat[1, 0])
    headers = [basic_text(v) for v in df.iloc[3].tolist()]
    rows = []
    for r in range(4, df.shape[0]):
        row_name = basic_text(df.iat[r, 0])
        if not row_name:
            continue
        rows.append({headers[c]: basic_text(df.iat[r, c]) for c in range(df.shape[1]) if headers[c]})
    return {
        'file': str(LEVEL_FILE),
        'sheet': sheet_name,
        'base_definitions': base_defs,
        'headers': headers,
        'records': rows,
    }


def main():
    data = {
        'skill_data': read_azure_skill_table(),
        'level_formula_data': {
            'azure': read_level_formula_table('碧之轨迹人物属性值与等级函数关系表'),
            'zero': read_level_formula_table('零之轨迹人物属性值与等级函数关系表'),
        },
        'notes': [
            'Skill text repaired by cp950->cp936 mojibake reversal.',
            'Level workbook contains attribute formulas by Lv, not an EXP threshold table.',
            'Skill table internal 编号/技能代码 need separate validation before mapping to save skill-slot IDs.',
        ],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(OUT)
    print('azure_skill_records', len(data['skill_data']['records']))
    print('azure_level_roles', len(data['level_formula_data']['azure']['records']))


if __name__ == '__main__':
    main()
