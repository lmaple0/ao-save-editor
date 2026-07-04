# 碧之轨迹 / Trails to Azure 存档编辑器

一个面向 NISA PC 版 **Ao no Kiseki / Trails to Azure** 的 Python/Tkinter 存档编辑器，可直接读写 zstd 压缩的 `savedata.dat`。

本项目基于原版工具 [`424778940z/BZH_AO_NO_KISEKI_Savedata_Editor`](https://github.com/424778940z/BZH_AO_NO_KISEKI_Savedata_Editor) 的偏移表、物品代码、校验和参考和怪物图鉴代码，并将其适配到 NISA 版存档格式。核心发现是：NISA 版 `savedata.dat` 不是加密文件，而是 zstd 压缩文件；解压后大小为 `0x2643C` 字节，与 BZH 原工具偏移表兼容。

## 版本与汉化说明

这个编辑器针对的是 NISA PC 版 **Trails to Azure** 的 `savedata.dat`。它不是欢乐百世简体中文 PC 版原始存档编辑器，也不是内存修改器。

编辑器里的中文物品名称、部分界面名称和代码表，主要取自欢乐百世简体中文 PC 版《碧之轨迹》以及 BZH 原工具数据。因此它们可能与以下文本不完全一致：

- NISA 英文版 **Trails to Azure** 的英文文本。
- 使用 [`J31why/zeroTool`](https://github.com/J31why/zeroTool) 等工具制作/应用的 NISA 版中文汉化补丁文本。

如果你游玩的是 NISA 版 Trails to Azure，并应用了 zeroTool 相关中文汉化补丁，请把本工具理解为“存档格式编辑器”。物品名和显示名用于辅助识别，遇到译名差异时应以物品代码、类别和游戏内实际效果为准。
<img width="616" height="534" alt="角色属性修改" src="https://github.com/user-attachments/assets/f5dfba14-3aea-4b85-8160-c81eccddec35" />
<img width="616" height="534" alt="物品修改" src="https://github.com/user-attachments/assets/1e9cbc55-6461-4520-93fa-edca41123b84" />
<img width="615" height="332" alt="基本修改" src="https://github.com/user-attachments/assets/a998b5ac-59d0-4ea2-b1bf-bfc5e402b451" />
<img width="616" height="534" alt="成就修改" src="https://github.com/user-attachments/assets/8c4d344b-bdee-4048-8ff5-9fabe61d2ffc" />
<img width="613" height="325" alt="战斗统计修改" src="https://github.com/user-attachments/assets/3018e8b1-f410-4349-96aa-d17aa2a8b2ba" />


## 已实现功能

- 直接打开和保存 zstd 压缩的 NISA `savedata.dat`。
- 修改 Mira、DP、代币、七属性耀晶片、游戏时间和难度。
- 修改 11 名角色的属性快照。
- 修改队伍槽位和 12 名角色/相关人物好感度。
- 浏览、搜索并重写完整 713 项物品表。
- 一键补齐并设置消耗品、食材、书籍、鱼、回路和装备数量。
- 修改 7 字节成就位图，支持全解锁/全锁定。
- 修改战斗手册统计计数。
- 修改 12 个角色显示外观槽位。
- 使用真实 BZH 怪物代码表一键全开怪物图鉴。
- 保存前重新计算 BZH 自定义 32 位累加和校验。
- 覆盖保存时自动创建 `.bak` 备份。

## 存档格式说明

- NISA 压缩存档测试样本约 4.6 KB。
- 解压后大小：`156,732` 字节，即 `0x2643C`。
- 用户存档校验和位置：
  - `0x26434`：存档数据 32 位累加和。
  - `0x26438`：文件大小校验值。
- 校验算法不是 CRC32，而是 BZH 原工具 `bzh_ank_se_savedata_checksum.h` 中的自定义 32 位累加和算法。
- 角色 HP/STR/DEF/ATS/ADF 等属性多半只是存档快照，读档后可能会被游戏根据等级、装备和核心回路重新计算。

NISA 版常见存档路径：

```text
C:/Users/<你的用户名>/Saved Games/FALCOM/Ao/dataXXXX/savedata.dat
```

## 环境要求

- Python 3.10+
- `zstandard`

安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

图形界面模式：

```bash
python ao_save_editor.py
```

命令行快速修改：

```bash
python ao_save_editor.py savedata.dat --mira 9999999 --sepith max --dp 400 --max-chars all --max-like
```

## 致谢

特别感谢 [`424778940z/BZH_AO_NO_KISEKI_Savedata_Editor`](https://github.com/424778940z/BZH_AO_NO_KISEKI_Savedata_Editor)。本项目的 NISA 适配离不开原 Qt/C++ 存档编辑器提供的偏移表、物品 ID、校验和算法参考和怪物图鉴代码数据。

也感谢 [`J31why/zeroTool`](https://github.com/J31why/zeroTool) 及其相关汉化工具生态，为 NISA 版 Crossbell 游戏的中文化提供了重要基础。

## 安全提示

修改存档前请手动备份。真实存档文件 `*.dat` 默认已加入 `.gitignore`，不建议提交到仓库。

更多开发排期和实现记录见 `ao_save_editor_roadmap.md`。
