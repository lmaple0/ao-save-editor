from pathlib import Path
import pandas as pd

DOWNLOADS = Path.home() / 'Downloads'
files = [
    DOWNLOADS / '碧轨魔法战技数据表0.099_201506142001.xlsx',
    DOWNLOADS / '零之轨迹&碧之轨迹 人物属性值与等级函数关系表Final20120629.xls',
]
for f in files:
    print('FILE', f)
    xl = pd.ExcelFile(f)
    print('SHEETS', xl.sheet_names)
    for s in xl.sheet_names[:12]:
        df = pd.read_excel(f, sheet_name=s, header=None, nrows=10)
        print('SHEET', s, df.shape)
        print(df.to_string(index=False, header=False))
        print('---')
