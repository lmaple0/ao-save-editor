from pathlib import Path
import json
import math
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'reference_workbook_summary.json'
skill_file = Path.home() / 'Downloads' / '碧轨魔法战技数据表0.099_201506142001.xlsx'
level_file = Path.home() / 'Downloads' / '零之轨迹&碧之轨迹 人物属性值与等级函数关系表Final20120629.xls'


def val(x):
    if pd.isna(x):
        return None
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x

skill = pd.read_excel(skill_file, sheet_name='碧之轨迹魔法战技详细数据表', header=None)
# Header row 0 contains the useful public columns.
headers = [str(x).strip() if not pd.isna(x) else f'col_{i}' for i, x in enumerate(skill.iloc[0].tolist())]
records = []
for idx in range(2, len(skill)):
    row = skill.iloc[idx]
    code_no = row.iloc[0]
    name = row.iloc[4]
    skill_code = row.iloc[33] if len(row) > 33 else None
    if pd.isna(code_no) and pd.isna(name) and pd.isna(skill_code):
        continue
    rec = {headers[i]: val(row.iloc[i]) for i in range(min(len(headers), len(row)))}
    rec['_row'] = idx + 1
    records.append(rec)

level_xl = pd.ExcelFile(level_file)
level_summaries = {}
for sheet in level_xl.sheet_names:
    df = pd.read_excel(level_file, sheet_name=sheet, header=None)
    text_hits = []
    for r in range(df.shape[0]):
        for c in range(df.shape[1]):
            cell = df.iat[r, c]
            if pd.isna(cell):
                continue
            s = str(cell)
            if any(k in s.lower() for k in ['exp', '经验', 'lv', '等级']):
                text_hits.append({'row': r + 1, 'col': c + 1, 'value': s})
    level_summaries[sheet] = {
        'shape': list(df.shape),
        'hits': text_hits[:80],
        'rows': [[val(x) for x in df.iloc[r].tolist()] for r in range(min(30, len(df)))]
    }

summary = {
    'skill_workbook': {
        'file': str(skill_file),
        'sheet': '碧之轨迹魔法战技详细数据表',
        'shape': list(skill.shape),
        'record_count': len(records),
        'columns': headers,
        'first_records': records[:30],
        'nonempty_skill_names': sum(1 for r in records if r.get('技能名称(名称翻译待逐渐修正)')),
        'nonempty_skill_codes': sum(1 for r in records if r.get('技能代码')),
    },
    'level_workbook': {
        'file': str(level_file),
        'sheets': level_summaries,
    }
}
OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(OUT)
print('skill_records', len(records), 'names', summary['skill_workbook']['nonempty_skill_names'], 'codes', summary['skill_workbook']['nonempty_skill_codes'])
for sheet, info in level_summaries.items():
    print(sheet, info['shape'], 'hits', len(info['hits']))
    for h in info['hits'][:10]:
        print(' ', h)
