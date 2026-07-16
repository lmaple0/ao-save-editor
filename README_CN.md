# 碧之轨迹 / Trails to Azure 存档编辑器

一个面向 NISA PC 版 **Ao no Kiseki / Trails to Azure** 的 Python/Tkinter 存档编辑器，可直接读写 zstd 压缩的 `savedata.dat`。

本项目基于原版工具 [`424778940z/BZH_AO_NO_KISEKI_Savedata_Editor`](https://github.com/424778940z/BZH_AO_NO_KISEKI_Savedata_Editor) 的偏移表、物品代码、校验和参考和怪物图鉴代码，并将其适配到 NISA 版存档格式。核心发现是：NISA 版 `savedata.dat` 不是加密文件，而是 zstd 压缩文件；解压后大小为 `0x2643C` 字节，与 BZH 原工具偏移表兼容。

## 版本与汉化说明

这个编辑器针对的是 NISA PC 版 **Trails to Azure** 的 `savedata.dat`。它不是欢乐百世简体中文 PC 版原始存档编辑器，也不是内存修改器。

编辑器里的中文物品名称、部分界面名称和代码表，运行时默认采用欢乐百世简体中文 PC 版《碧之轨迹》以及 BZH 原工具数据；物品名按存档物品 ID 以 [Ouroboros/Falcom ItemNameMap.py](https://github.com/Ouroboros/Falcom/blob/master/ED7/Decompiler/GameData/ItemNameMap.py) 为准。结构化物品索引同时保留了经过保守匹配的 CLE/云豹中文译名，供对照使用；当前 GUI 不提供 CLE 译名切换。当前 GUI 已支持全局中文/英文/日文切换，覆盖已实现的标签页、按钮、角色名、耀晶片名、战斗统计、成就、角色外观、快捷操作以及已匹配的物品/成就名称；缺失英日名时回退到中文。因此它们仍可能与以下文本不完全一致：

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
- 修改人物装备和 7 个回路槽，采用与背包数量同步的事务写入；下拉候选会强制执行武器/槽位类别、核心回路唯一性、普通回路防重复，以及根据 NISA `t_orb` 与 `t_quartz` 主元素解析出的属性限定。
- 修改队伍槽位和 12 名角色/相关人物好感度。
- GUI 已支持中文/英文/日文全局切换，覆盖已实现的控件文本和数据名称。
- 浏览、搜索并重写完整 713 项物品表；可按 ID/名称将一个物品替换成另一个物品，并将数量设为 0–99 的任意整数；物品名支持中文/英文/日文显示切换。
- 修改 24 道基础菜谱的料理手册解锁状态，支持逐项勾选、全选/全不选，并随全局语言切换显示欢乐百世中文、NISA 英文和 Falcom 日文名称。
- 钓鱼手册显示 31 种鱼的登记状态、最大尺寸、自然范围、累计次数，以及三语奖励/鱼饵名称；支持单项登记、未登记、精确最大尺寸和全部登记，奖励与鱼饵资料保持只读。
- 一键补齐并设置消耗品、食材、书籍、鱼、回路和装备数量。
- 修改 NISA 单存档 `0x1F454~0x1F45A` 的 56 位成就位图，显示已解锁数量，支持全解锁/全锁定及中文/英文/日文名称切换。
- 修改战斗手册统计计数。
- 修改 12 个固定角色的外观资源槽，使用已校正的 NISA 原始 ID，覆盖瓦吉前/后期、银/莉夏及间章泳装变体。
- 怪物图鉴支持 305 项目录浏览、名称/代码/文件/地点搜索、75 个细分地点筛选、状态诊断、逐项编辑和一键全开；新增只读详情面板，显示 HP/EP/CP、完整战斗属性、七属性有效率、异常抗性、掉落耀晶片、掉落物、战技名称、说明及 `ms/as` 来源。详情由本机 NISA 三语 333 个 `ms*.dat` 生成，数值结构跨语言一致。
- 新增独立于存档的只读“资源索引”研究页：可按中/日/英文名称、角色/怪物代码、`ms*.dat`、`as*.dat` 和动作入口反向搜索 36 个角色、305 个存档怪物、333 个状态文件、276 个动作脚本、1052 条战技与 4171 个非空动作入口；显示关系来源与“已验证/候选”可信度，并保留未解析战技引用，不提供任何写入按钮。
- 只读宝箱进度查看器覆盖 280 个宝箱和 44 张地图，支持按三语地图/物品名称搜索、地图筛选、仅显示缺失宝箱，并显示宝箱坐标、触发坐标和触发范围。宝箱旗标来自存档场景旗标区；地点名称由本机 NISA 三语 	_town._dt 按场景 MapIndex 生成。
- 新增中/英/日只读存档诊断页，检查大小、校验和、难度、物品、队伍、外观、料理镜像、怪物记录和参考数据版本；只报告问题，不自动修复或写回。
- 保存前重新计算 BZH 自定义 32 位累加和校验。
- 覆盖保存时自动创建 `.bak` 备份。

## 当前实现与验证记录

最近一轮 review 修复了几类会影响存档安全或界面一致性的 bug：

- 角色属性编辑现在只对 HP/EXP 写入 `u32`，等级、EP、CP、STR、DEF、ATS、ADF 等字段按 `u16` 写入，避免覆盖相邻字段。
- 角色属性输入框失焦写回现在直接读取当前输入框内容，修复原先 Tk `textvariable` 查找错误导致的静默失败。
- 未打开存档时，物品刷新、成就全解锁/全锁定、怪物图鉴全开和各类快捷操作会给出明确状态提示。
- 拆分“时”在耀晶片 Time 与游戏时间小时中的不同语义，避免英文/日文翻译互相覆盖。
- 队员槽位标签和快捷操作角色名会跟随全局语言切换刷新。
- 怪物记录按完整 8 字节结构读取和重写；未知代码与未选择记录原样保留，容量不足时拒绝写入，不会静默丢弃。4 个状态字节只识别已验证的完整资料值 `08 FE FF FF`，暂不猜测子位语义。

已完成的验证：

- workspace 与 publish 两份脚本均通过 `py_compile`。
- 本地化字典通过重复 key 检查。
- 样例存档完成加载、读取物品、写回、zstd 保存、再次加载的 roundtrip。
- CLI 在临时存档副本上验证了 `--mira`、`--dp`、`--sepith max`、`--max-like`。
- 料理手册已用 9 个真实进度存档验证 0/1/6/8/12/13/15/18/18 项读取结果，并在临时副本上完成 24 项全选、校验和重算、zstd 保存和重新加载 roundtrip。
- 本机 Windows Python 3.13 GUI 冒烟测试已验证 24 个复选框、标签页及中文/英文/日文菜名切换。
- 怪物目录生成器完成 305/305 存档代码、三语 `ms*.dat` 名称及三语地点覆盖校验（上游启用 283、注释待复核 22；场景直取 302、本地地点表补充 3）；23 项单元测试覆盖三语本地化、目录、名称/地点搜索、地点来源、部分/重复/未知诊断、逐项写入、全开容量保护和记录区尾边界。
- 怪物详情生成器完成三语 333/333 文件解析和全数值结构对比，305/305 存档图鉴怪物可关联详情，333/333 有有效动作脚本来源；`ms60000/ms60001` 的未解释尾部扩展只记录大小与哈希。详情 JSON 改为首次查看时懒加载。
- 资源索引生成器独立、带边界检查地解析三语 `t_name._dt` 和有效 `as*.dat` 头/动作表，不反汇编或执行动作指令；生成 6173 个节点、6835 条关系及 7 组同名候选变体。5.4 MB 索引按首次打开页面懒加载，空搜索最多向 Treeview 填充 500 项。
- 宝箱目录生成器完成 280/280 旗标、44/44 三语地图和 93/93 NISA 场景文件覆盖；两个本机 NISA 样例存档均解析为 117/280 已取得。宝箱功能只读取旗标，不写入存档。
- 当前 118 项单元测试全部通过，新增 4 项 `tools/`、`docs/` 目录契约检查；其中成就回归测试覆盖 47/56 实际位图、ID 完整性、本地化匹配及仅修改 7 字节的写入边界。用户标注的 8 个队伍样本与原始槽位顺序逐项一致；122 个有效本机存档均无未知队伍/外观 ID，且只读验证前后哈希不变；128 个有效本机存档的元素限定检查为零冲突，Windows Python 3.13 隐藏窗口测试确认限定槽只显示兼容回路。

Codex bundled Python 缺少 Tcl/Tk；GUI 已改用本机 Windows Python 3.13 完成隐藏窗口构建与三语切换冒烟测试。

## 本地化数据

- `ao_item_i18n.json`：按存档物品 ID 匹配的物品名称/描述。
- `ao_item_index.json`：结构化物品元数据；`zh_joyoland` 是运行时中文默认值，`zh_cle` 是保守保留的对照层。
- `ao_achievement_i18n.json`：本地化条目按 `game_achievement_id` 关联；其中 `bitmap_part`/`bit` 只保留欢乐百世系统存档的来源坐标，并非 NISA 单存档位序。NISA 的 56 位按 `ao.exe` 平台表第 1–56 项排列（第 0 项是总成就），再关联到这些 ID。
- `ao_magic_i18n.json`：来自用户提供 magic CSV 的战技/导力魔法英文行数据。这里的 CSV 行号只是参考行，不声明为已确认的存档战技槽位 ID；日文 CSV 文本已保留，但存在需要后续复核的编码问题。
- `ao_monster_reference.json`：由 `tools/build_monster_reference.py` 将存档代码表、Ouroboros/Falcom 身份层、本机 NISA 三语 `ms*.dat` 名称和场景地点合并生成；不执行上游 Python 文件。`tools/build_monster_locations.py` 负责场景代码扫描和三语 MapIndex 地点解析。
- `ao_monster_details.json`：由 `tools/build_monster_details.py` 使用独立、带边界检查的只读解析器从本机三语 333 个 `ms*.dat` 生成；保留每个来源文件的 SHA-256，不执行或分发上游生成脚本及原始游戏文件。
- `ao_reference_graph.json`：由 `tools/build_reference_graph.py` 连接怪物目录、三语 `t_name._dt`、333 个 `ms` 与三语有效 `as` 动作表；保留相对来源路径和 SHA-256。动作入口按索引关联，不能证明属于本地脚本的战技引用只列为未解析研究项。
- `ao_chest_reference.json`：由 `tools/build_chest_reference.py` 将 Ouroboros/Falcom RecordViewer 的宝箱旗标与坐标、本机 NISA 场景 `MapIndex`、三语 `t_town._dt` 和物品 ID 索引合并生成；保留旧 Joyoland 地图/物品名与源码行号作为来源证据。

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

也感谢 [`Ouroboros/Falcom`](https://github.com/Ouroboros/Falcom/tree/master/ED7/Decompiler) 提供可追溯的 ED7 数据格式、怪物状态目录和反编译工具，以及 [`J31why/zeroTool`](https://github.com/J31why/zeroTool) 及其相关汉化工具生态。

## 安全提示

修改存档前请手动备份。真实存档文件 `*.dat` 默认已加入 `.gitignore`，不建议提交到仓库。

更多开发排期和实现记录见 `docs/ao_save_editor_roadmap.md`。
