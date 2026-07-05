#!/usr/bin/env python3
"""
碧之轨迹 NISA版 存档修改器 (基于 BZH_AO_NO_KISEKI_Savedata_Editor 偏移表)
直接支持 zstd 压缩的 savedata.dat 文件。
"""

import struct
import os
import sys
import io
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

try:
    import zstandard as zstd
except ImportError as exc:
    zstd = None
    ZSTD_IMPORT_ERROR = exc
else:
    ZSTD_IMPORT_ERROR = None

# 物品数据库 (由 BZH 代码定义自动生成)
try:
    from ao_items_db import ITEM_DB
except ImportError:
    ITEM_DB = {}

ITEM_LANGUAGE_LABELS = {
    "zh_cn": "中文",
    "en": "English",
    "ja": "日本語",
}


def app_dir():
    return APP_DIR


def load_item_i18n():
    path = os.path.join(app_dir(), "ao_item_i18n.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    rows = data.get("items", []) if isinstance(data, dict) else []
    result = {}
    for row in rows:
        try:
            code = int(row.get("id_dec"))
        except (TypeError, ValueError):
            continue
        result[code] = row
    return result


ITEM_I18N = load_item_i18n()


def load_achievement_i18n():
    path = os.path.join(app_dir(), "ao_achievement_i18n.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    rows = data.get("achievements", []) if isinstance(data, dict) else []
    result = {}
    for row in rows:
        try:
            key = (int(row.get("bitmap_part")), int(row.get("bit")))
        except (TypeError, ValueError):
            continue
        result[key] = row
    return result


ACHIEVEMENT_I18N = load_achievement_i18n()
APP_TITLES = {
    "zh_cn": "碧之轨迹 NISA版 存档修改器",
    "en": "Trails to Azure NISA Save Editor",
    "ja": "碧の軌跡 NISA版 セーブエディタ",
}

CHARACTER_NAME_I18N = {
    "Lloyd": {"zh_cn": "罗伊德", "en": "Lloyd", "ja": "ロイド"},
    "Elie": {"zh_cn": "艾莉", "en": "Elie", "ja": "エリィ"},
    "Tio": {"zh_cn": "缇欧", "en": "Tio", "ja": "ティオ"},
    "Randy": {"zh_cn": "兰迪", "en": "Randy", "ja": "ランディ"},
    "Wazy": {"zh_cn": "瓦吉", "en": "Wazy", "ja": "ワジ"},
    "Rixia": {"zh_cn": "莉夏", "en": "Rixia", "ja": "リーシャ"},
    "Zeit": {"zh_cn": "蔡特", "en": "Zeit", "ja": "ツァイト"},
    "Arios": {"zh_cn": "亚里欧斯", "en": "Arios", "ja": "アリオス"},
    "Noel": {"zh_cn": "诺艾尔", "en": "Noel", "ja": "ノエル"},
    "Dudley": {"zh_cn": "达德利", "en": "Dudley", "ja": "ダドリー"},
    "Garcia": {"zh_cn": "加尔西亚", "en": "Garcia", "ja": "ガルシア"},
    "琪雅": {"zh_cn": "琪雅", "en": "KeA", "ja": "キーア"},
    "艾莉": {"zh_cn": "艾莉", "en": "Elie", "ja": "エリィ"},
    "缇欧": {"zh_cn": "缇欧", "en": "Tio", "ja": "ティオ"},
    "兰迪": {"zh_cn": "兰迪", "en": "Randy", "ja": "ランディ"},
    "诺艾尔": {"zh_cn": "诺艾尔", "en": "Noel", "ja": "ノエル"},
    "瓦吉": {"zh_cn": "瓦吉", "en": "Wazy", "ja": "ワジ"},
    "莉夏": {"zh_cn": "莉夏", "en": "Rixia", "ja": "リーシャ"},
    "达德利": {"zh_cn": "达德利", "en": "Dudley", "ja": "ダドリー"},
    "伊莉雅": {"zh_cn": "伊莉雅", "en": "Ilya", "ja": "イリア"},
    "塞西尔": {"zh_cn": "塞西尔", "en": "Cecile", "ja": "セシル"},
    "芙兰": {"zh_cn": "芙兰", "en": "Fran", "ja": "フラン"},
    "苏莉": {"zh_cn": "苏莉", "en": "Sully", "ja": "シャーリィ"},
    "银": {"zh_cn": "银", "en": "Silver", "ja": "銀"},
    "秦": {"zh_cn": "秦", "en": "Xin", "ja": "シン"},
    "雷蒙德": {"zh_cn": "雷蒙德", "en": "Raymond", "ja": "レイモンド"},
    "罗伊德": {"zh_cn": "罗伊德", "en": "Lloyd", "ja": "ロイド"},
    "艾约": {"zh_cn": "艾约", "en": "Ayo", "ja": "エア"},
}


def character_name(name, lang="zh_cn"):
    return CHARACTER_NAME_I18N.get(name, {}).get(lang) or name


UI_TRANSLATIONS = {
    "zh_cn": {
        "打开存档 (savedata.dat)": "打开存档 (savedata.dat)",
        "保存存档": "保存存档",
        "未加载存档": "未加载存档",
        "语言": "语言",
        "基本 / Mira": "基本 / Mira",
        "角色属性": "角色属性",
        "队伍 / 好感度": "队伍 / 好感度",
        "物品": "物品",
        "成就": "成就",
        "战斗手册": "战斗手册",
        "角色外观": "角色外观",
        "快捷操作": "快捷操作",
        "资源": "资源",
        "耀晶片": "耀晶片",
        "游戏时间": "游戏时间",
        "难度 (0=Easy 1=Normal 2=Hard 3=Nightmare)": "难度 (0=Easy 1=Normal 2=Hard 3=Nightmare)",
        "角色": "角色",
        "队伍编成 (0=罗伊德, 1=艾莉, ..., 255=空)": "队伍编成 (0=罗伊德, 1=艾莉, ..., 255=空)",
        "好感度 (0-? )": "好感度 (0-? )",
        "搜索:": "搜索:",
        "过滤": "过滤",
        "全部显示": "全部显示",
        "名称语言:": "名称语言:",
        "选中 → 99": "选中 → 99",
        "选中 → 0": "选中 → 0",
        "代码": "代码",
        "名称": "名称",
        "数量": "数量",
        "一键操作 (先打开存档!)": "一键操作 (先打开存档!)",
        "Max 资源": "Max 资源",
        "Mira → 9,999,999": "Mira → 9,999,999",
        "全耀晶片 → 9,999": "全耀晶片 → 9,999",
        "DP → 400": "DP → 400",
        "Max 队伍角色": "Max 队伍角色",
        "好感度一键满": "好感度一键满",
        "全员好感度 → 255": "全员好感度 → 255",
        "Max 物品": "Max 物品",
        "全消耗品/食材/书籍 → 99": "全消耗品/食材/书籍 → 99",
        "全回路 → 99 (含核心回路)": "全回路 → 99 (含核心回路)",
        "全装备 → 1": "全装备 → 1",
        "怪物图鉴": "怪物图鉴",
        "一键全开怪物图鉴": "一键全开怪物图鉴",
        "全解锁": "全解锁",
        "全锁定": "全锁定",
        "战斗统计数据 (修改后保存生效)": "战斗统计数据 (修改后保存生效)",
        "角色显示外观 (修改对应槽位的模型)": "角色显示外观 (修改对应槽位的模型)",
        "显示1": "显示1", "显示2": "显示2", "显示3": "显示3", "显示4": "显示4",
        "显示5": "显示5", "显示6": "显示6", "显示7": "显示7", "显示8": "显示8",
        "显示9": "显示9", "显示10": "显示10", "显示11": "显示11", "显示12": "显示12",
        "Mira": "Mira", "DP": "DP", "Medal": "Medal",
        "总秒数": "总秒数", "时": "时", "分": "分", "秒": "秒",
        "难度": "难度",
        "全成就已解锁": "全成就已解锁",
        "全成就已锁定": "全成就已锁定",
        "怪物图鉴已全开 · 请保存存档": "怪物图鉴已全开 · 请保存存档",
        "选择 savedata.dat": "选择 savedata.dat",
        "错误": "错误",
        "提示": "提示",
        "保存为": "保存为",
        "完成": "完成",
        "请先打开存档文件": "请先打开存档文件",
        "无法解析存档:\n{fp}\n\n文件可能是加密的或格式不正确。": "无法解析存档:\n{fp}\n\n文件可能是加密的或格式不正确。",
        "存档已保存到:\n{fp}\n\n备份已自动创建为 .bak\n请将文件放回游戏存档目录替换原文件。": "存档已保存到:\n{fp}\n\n备份已自动创建为 .bak\n请将文件放回游戏存档目录替换原文件。",
        "已设置 {varname} = {val}": "已设置 {varname} = {val}",
        "全耀晶片 → 9999": "全耀晶片 → 9999",
        "{name} 已满属性": "{name} 已满属性",
        "全员好感度 → 255": "全员好感度 → 255",
        "全消耗品/食材/书籍/鱼 → 99": "全消耗品/食材/书籍/鱼 → 99",
        "全回路 → 99": "全回路 → 99",
        "全装备 → 1": "全装备 → 1",
        "已加载: ...{fdir}/{fname}  ({size} bytes)": "已加载: ...{fdir}/{fname}  ({size} bytes)",
        "已保存到: {fp}": "已保存到: {fp}",
        "地": "地",
        "水": "水",
        "火": "火",
        "风": "风",
        "时": "时",
        "空": "空",
        "幻": "幻",
        "最大HP": "最大HP",
        "当前HP": "当前HP",
        "等级": "等级",
        "最大EP": "最大EP",
        "当前EP": "当前EP",
        "CP": "CP",
        "EXP": "EXP",
        "STR": "STR",
        "DEF": "DEF",
        "ATS": "ATS",
        "ADF": "ADF",
        "战斗次数": "战斗次数",
        "失败次数": "失败次数",
        "胜利次数": "胜利次数",
        "逃跑次数": "逃跑次数",
        "重试战斗次数": "重试战斗次数",
        "S战技使用次数": "S战技使用次数",
        "组合战技次数": "组合战技次数",
        "先制攻击次数": "先制攻击次数",
        "被偷袭次数": "被偷袭次数",
        "杀敌数": "杀敌数",
        "爆灵次数": "爆灵次数",
        "队员 {num}": "队员 {num}",
        "{name} LV99 满HP/EP/CP": "{name} LV99 满HP/EP/CP",
    },
    "en": {
        "打开存档 (savedata.dat)": "Open savedata.dat",
        "保存存档": "Save",
        "未加载存档": "No save loaded",
        "语言": "Language",
        "基本 / Mira": "Basics / Mira",
        "角色属性": "Characters",
        "队伍 / 好感度": "Party / Bond",
        "物品": "Items",
        "成就": "Achievements",
        "战斗手册": "Battle Notebook",
        "角色外观": "Appearance",
        "快捷操作": "Quick Actions",
        "资源": "Resources",
        "耀晶片": "Sepith",
        "游戏时间": "Play Time",
        "难度 (0=Easy 1=Normal 2=Hard 3=Nightmare)": "Difficulty (0=Easy 1=Normal 2=Hard 3=Nightmare)",
        "角色": "Character",
        "队伍编成 (0=罗伊德, 1=艾莉, ..., 255=空)": "Party formation (0=Lloyd, 1=Elie, ..., 255=empty)",
        "好感度 (0-? )": "Bond values (0-? )",
        "搜索:": "Search:",
        "过滤": "Filter",
        "全部显示": "Show All",
        "名称语言:": "Name Language:",
        "选中 → 99": "Selected → 99",
        "选中 → 0": "Selected → 0",
        "代码": "Code",
        "名称": "Name",
        "数量": "Qty",
        "一键操作 (先打开存档!)": "Quick actions (open a save first!)",
        "Max 资源": "Max Resources",
        "Mira → 9,999,999": "Mira → 9,999,999",
        "全耀晶片 → 9,999": "All Sepith → 9,999",
        "DP → 400": "DP → 400",
        "Max 队伍角色": "Max Party Characters",
        "好感度一键满": "Max Bond",
        "全员好感度 → 255": "All bond values → 255",
        "Max 物品": "Max Items",
        "全消耗品/食材/书籍 → 99": "Consumables/ingredients/books → 99",
        "全回路 → 99 (含核心回路)": "All quartz → 99 (core quartz included)",
        "全装备 → 1": "All equipment → 1",
        "怪物图鉴": "Monster Manual",
        "一键全开怪物图鉴": "Unlock all monster records",
        "全解锁": "Unlock All",
        "全锁定": "Lock All",
        "战斗统计数据 (修改后保存生效)": "Battle statistics (changes apply on save)",
        "角色显示外观 (修改对应槽位的模型)": "Character appearance slots (edit the model for each slot)",
        "显示1": "Slot 1", "显示2": "Slot 2", "显示3": "Slot 3", "显示4": "Slot 4",
        "显示5": "Slot 5", "显示6": "Slot 6", "显示7": "Slot 7", "显示8": "Slot 8",
        "显示9": "Slot 9", "显示10": "Slot 10", "显示11": "Slot 11", "显示12": "Slot 12",
        "Mira": "Mira", "DP": "DP", "Medal": "Medal",
        "总秒数": "Total seconds", "时": "h", "分": "m", "秒": "s",
        "难度": "Difficulty",
        "全成就已解锁": "All achievements unlocked",
        "全成就已锁定": "All achievements locked",
        "怪物图鉴已全开 · 请保存存档": "Monster manual unlocked · save the file",
        "选择 savedata.dat": "Choose savedata.dat",
        "错误": "Error",
        "提示": "Notice",
        "保存为": "Save As",
        "完成": "Done",
        "请先打开存档文件": "Open a save file first",
        "无法解析存档:\n{fp}\n\n文件可能是加密的或格式不正确。": "Could not parse save:\n{fp}\n\nThe file may be encrypted or malformed.",
        "存档已保存到:\n{fp}\n\n备份已自动创建为 .bak\n请将文件放回游戏存档目录替换原文件。": "Save written to:\n{fp}\n\nA .bak backup was created automatically. Replace the original in the game save folder.",
        "已设置 {varname} = {val}": "Set {varname} = {val}",
        "全耀晶片 → 9999": "All Sepith → 9999",
        "{name} 已满属性": "{name} maxed",
        "全员好感度 → 255": "All bond values → 255",
        "全消耗品/食材/书籍/鱼 → 99": "Consumables/ingredients/books/fish → 99",
        "全回路 → 99": "All quartz → 99",
        "全装备 → 1": "All equipment → 1",
        "已加载: ...{fdir}/{fname}  ({size} bytes)": "Loaded: ...{fdir}/{fname}  ({size} bytes)",
        "已保存到: {fp}": "Saved to: {fp}",
        "地": "Earth",
        "水": "Water",
        "火": "Fire",
        "风": "Wind",
        "时": "Time",
        "空": "Space",
        "幻": "Mirage",
        "最大HP": "MAX HP",
        "当前HP": "Current HP",
        "等级": "Level",
        "最大EP": "MAX EP",
        "当前EP": "Current EP",
        "CP": "CP",
        "EXP": "EXP",
        "STR": "STR",
        "DEF": "DEF",
        "ATS": "ATS",
        "ADF": "ADF",
        "战斗次数": "Total Battles Fought",
        "失败次数": "Character K.O.s Suffered",
        "胜利次数": "Victories",
        "逃跑次数": "Times Escaped",
        "重试战斗次数": "Battles Retried",
        "S战技使用次数": "S-Breaks Used",
        "组合战技次数": "Support Crafts Used",
        "先制攻击次数": "Party Advantages Gained",
        "被偷袭次数": "Enemy Advantages Suffered",
        "杀敌数": "Enemies Slain",
        "爆灵次数": "Burst Uses",
        "队员 {num}": "Member {num}",
        "{name} LV99 满HP/EP/CP": "{name} Lv99 Max HP/EP/CP",
    },
    "ja": {
        "打开存档 (savedata.dat)": "セーブデータを開く (savedata.dat)",
        "保存存档": "保存",
        "未加载存档": "未読込",
        "语言": "言語",
        "基本 / Mira": "基本 / ミラ",
        "角色属性": "キャラクター",
        "队伍 / 好感度": "編成 / 絆",
        "物品": "アイテム",
        "成就": "実績",
        "战斗手册": "戦闘手帳",
        "角色外观": "外見",
        "快捷操作": "クイック操作",
        "资源": "資源",
        "耀晶片": "セピス",
        "游戏时间": "プレイ時間",
        "难度 (0=Easy 1=Normal 2=Hard 3=Nightmare)": "難易度 (0=Easy 1=Normal 2=Hard 3=Nightmare)",
        "角色": "キャラ",
        "队伍编成 (0=罗伊德, 1=艾莉, ..., 255=空)": "編成 (0=ロイド, 1=エリィ, ..., 255=空)",
        "好感度 (0-? )": "絆値 (0-? )",
        "搜索:": "検索:",
        "过滤": "絞り込み",
        "全部显示": "全表示",
        "名称语言:": "名称言語:",
        "选中 → 99": "選択 → 99",
        "选中 → 0": "選択 → 0",
        "代码": "コード",
        "名称": "名称",
        "数量": "数量",
        "一键操作 (先打开存档!)": "クイック操作 (先にセーブを開いてください!)",
        "Max 资源": "資源最大化",
        "Mira → 9,999,999": "ミラ → 9,999,999",
        "全耀晶片 → 9,999": "全セピス → 9,999",
        "DP → 400": "DP → 400",
        "Max 队伍角色": "編成キャラ最大化",
        "好感度一键满": "絆値最大化",
        "全员好感度 → 255": "全員絆値 → 255",
        "Max 物品": "アイテム最大化",
        "全消耗品/食材/书籍 → 99": "消耗品/食材/書籍 → 99",
        "全回路 → 99 (含核心回路)": "全クオーツ → 99 (コアクオーツ含む)",
        "全装备 → 1": "装備 → 1",
        "怪物图鉴": "魔兽图鉴",
        "一键全开怪物图鉴": "魔兽图鉴を全開放",
        "全解锁": "全解除",
        "全锁定": "全固定",
        "战斗统计数据 (修改后保存生效)": "戦闘統計 (変更は保存時に反映)",
        "角色显示外观 (修改对应槽位的模型)": "キャラ外見スロット (モデルを変更)",
        "显示1": "スロット1", "显示2": "スロット2", "显示3": "スロット3", "显示4": "スロット4",
        "显示5": "スロット5", "显示6": "スロット6", "显示7": "スロット7", "显示8": "スロット8",
        "显示9": "スロット9", "显示10": "スロット10", "显示11": "スロット11", "显示12": "スロット12",
        "Mira": "ミラ", "DP": "DP", "Medal": "メダル",
        "总秒数": "合計秒", "时": "時", "分": "分", "秒": "秒",
        "难度": "難易度",
        "全成就已解锁": "実績を全解除",
        "全成就已锁定": "実績を全固定",
        "怪物图鉴已全开 · 请保存存档": "魔兽图鉴を全開放しました · セーブしてください",
        "选择 savedata.dat": "savedata.dat を選択",
        "错误": "エラー",
        "提示": "通知",
        "保存为": "名前を付けて保存",
        "完成": "完了",
        "请先打开存档文件": "先にセーブを開いてください",
        "无法解析存档:\n{fp}\n\n文件可能是加密的或格式不正确。": "セーブを解析できません:\n{fp}\n\n暗号化されているか、形式が正しくない可能性があります。",
        "存档已保存到:\n{fp}\n\n备份已自动创建为 .bak\n请将文件放回游戏存档目录替换原文件。": "セーブを書き込みました:\n{fp}\n\n.bak バックアップを自動作成しました。ゲームのセーブフォルダに戻してください。",
        "已设置 {varname} = {val}": "{varname} = {val} に設定",
        "全耀晶片 → 9999": "全セピス → 9999",
        "{name} 已满属性": "{name} 最大化",
        "全员好感度 → 255": "全員絆値 → 255",
        "全消耗品/食材/书籍/鱼 → 99": "消耗品/食材/書籍/魚 → 99",
        "全回路 → 99": "全クオーツ → 99",
        "全装备 → 1": "装備 → 1",
        "已加载: ...{fdir}/{fname}  ({size} bytes)": "読込済み: ...{fdir}/{fname}  ({size} bytes)",
        "已保存到: {fp}": "保存先: {fp}",
        "地": "地",
        "水": "水",
        "火": "火",
        "风": "風",
        "时": "時",
        "空": "空",
        "幻": "幻",
        "最大HP": "最大HP",
        "当前HP": "現在HP",
        "等级": "レベル",
        "最大EP": "MAX EP",
        "当前EP": "現在EP",
        "CP": "CP",
        "EXP": "EXP",
        "STR": "STR",
        "DEF": "DEF",
        "ATS": "ATS",
        "ADF": "ADF",
        "战斗次数": "戦闘回数",
        "失败次数": "戦闘不能回数",
        "胜利次数": "勝利回数",
        "逃跑次数": "逃走回数",
        "重试战斗次数": "再戦回数",
        "S战技使用次数": "Sクラフト使用回数",
        "组合战技次数": "サポートクラフト使用回数",
        "先制攻击次数": "先制攻撃回数",
        "被偷袭次数": "奇襲を受けた回数",
        "杀敌数": "撃破数",
        "爆灵次数": "バースト使用回数",
        "队员 {num}": "メンバー {num}",
        "{name} LV99 满HP/EP/CP": "{name} Lv99 HP/EP/CP最大",
    },
}

# ============================================================
# BZH 工具偏移表 (bzh_ank_se_offset_define.h)
# ============================================================

# 角色基址 (max_hp = 基址+0)
CHAR_BASES = {
    "Lloyd":  0x00000094,
    "Elie":   0x000000C8,
    "Tio":    0x000000FC,
    "Randy":  0x00000130,
    "Wazy":   0x00000164,   # Lazy
    "Rixia":  0x00000198,
    "Zeit":   0x000001CC,
    "Arios":  0x00000200,
    "Noel":   0x00000234,
    "Dudley": 0x00000268,
    "Garcia": 0x0000029C,
}

# 角色属性偏移 (相对于角色基址)
CHAR_ATTR = {
    "max_hp": 0x00,  # uint32
    "hp":     0x04,  # uint32
    "lv":     0x08,  # uint16
    "max_ep": 0x0A,  # uint16
    "ep":     0x0C,  # uint16
    "cp":     0x0E,  # uint16
    "exp":    0x10,  # uint32
    "str":    0x14,  # uint16
    "def":    0x16,  # uint16
    "ats":    0x18,  # uint16
    "adf":    0x1A,  # uint16
}

# 资源和进度偏移
OFFSETS = {
    "mira":      0x00019C2C,
    "medal":     0x00019C34,
    "dp":        0x00019C1C,
    "time_s":    0x00019C84,
    "difficulty":0x0001F36D,
}

# 七属性耀晶片
SEPITH_OFFSETS = {
    "地": 0x00019C3C,
    "水": 0x00019C40,
    "火": 0x00019C44,
    "风": 0x00019C48,
    "时": 0x00019C4C,
    "空": 0x00019C50,
    "幻": 0x00019C54,
}

# 好感度
LIKEABILITY = {
    "琪雅": 0x0001B334, "艾莉": 0x0001B335, "缇欧": 0x0001B336,
    "兰迪": 0x0001B337, "诺艾尔": 0x0001B338, "瓦吉": 0x0001B339,
    "莉夏": 0x0001B33A, "达德利": 0x0001B33B, "伊莉雅": 0x0001B33C,
    "塞西尔": 0x0001B33D, "芙兰": 0x0001B33E, "苏莉": 0x0001B33F,
}

# 队伍槽位 (8个, 每个2字节)
TEAM_SLOTS = [0x0001AFE0 + i * 2 for i in range(8)]

# 校验和
CHECKSUM_USER_SIZE = 0x00026438
CHECKSUM_USER = 0x00026434

# 期望的存档体积
EXPECTED_SIZE = 0x2643C  # 156732 bytes

# 团队队员ID映射
# 物品列表偏移 (BZH: 0xE2C ~ 0x194C, 每项 4 字节: u16 code + u16 qty)
ITEMS_START = 0x00000E2C
ITEMS_END   = 0x0000194C

# BZH 写入顺序 — 按此顺序序列化物品 (数量为0则跳过)
ITEM_WRITE_ORDER = [
    # 道具 - 普通
    [0x01f4,0x01f5,0x01f6,0x01f7,0x01f8,0x01f9,0x01fa,0x01fb,0x01fc,0x01fd,0x01fe,0x01ff,0x0200,0x0201,0x0202,0x0203,0x0204,0x0205,0x0206,0x0207,0x0208,0x0209,0x020a,0x020b,0x020c,0x020d,0x020e,0x020f,0x0210,0x0211,0x0212,0x0213,0x0214,0x0216,0x0217,0x0218,0x0219,0x021a,0x021b,0x021c,0x021d],
    # 道具 - 料理
    [0x0190,0x0191,0x0192,0x0193,0x0194,0x0195,0x0196,0x0197,0x0198,0x0199,0x019a,0x019b,0x019c,0x019d,0x019e,0x019f,0x01a0,0x01a1,0x01a2,0x01a3,0x01a4,0x01a5,0x01a6,0x01a7,0x01a8,0x01a9,0x01aa,0x01ab,0x01ac,0x01ad,0x01ae,0x01af,0x01b0,0x01b1,0x01b2,0x01b3,0x01b4,0x01b5,0x01b6,0x01b7,0x01b8,0x01b9,0x01ba,0x01bb,0x01bc,0x01bd,0x01be,0x01bf,0x01c0,0x01c1,0x01c2,0x01c3,0x01c4,0x01c5,0x01c6,0x01c7,0x01c8,0x01c9,0x01ca,0x01cb,0x01cc,0x01cd,0x01ce,0x01cf,0x01d0,0x01d1,0x01d2,0x01d3,0x01d4,0x01d5,0x01d6,0x01d7,0x01d8,0x01d9],
    # 装备 - 武器 (通用)
    [0x0009],
    # 武器 - 罗伊德
    [0x03e8,0x03e9,0x03ea,0x03eb,0x03ec,0x03ed,0x03ee,0x03ef,0x03f0,0x03f1,0x03f2,0x03f3,0x03f4,0x03f5,0x03f6],
    # 武器 - 艾莉
    [0x03fd,0x03fe,0x03ff,0x0400,0x0401,0x0402,0x0403,0x0404,0x0405,0x0406,0x0407,0x0408,0x0409],
    # 武器 - 缇欧
    [0x0413,0x0414,0x0415,0x0416,0x0417,0x0418,0x0419,0x041a,0x041b,0x041c,0x041d],
    # 武器 - 兰迪
    [0x0425,0x0427,0x0428,0x0429,0x042a,0x042b,0x042c,0x042d,0x042e,0x042f,0x0430,0x0431],
    # 武器 - 瓦吉
    [0x0439,0x043a,0x043b,0x043c,0x043d,0x043e,0x043f,0x0440,0x0441,0x0442,0x0443,0x0444,0x0445],
    # 武器 - 诺埃尔
    [0x044c,0x044d,0x044e,0x044f,0x0450,0x0451,0x0452,0x0453,0x0454,0x0455,0x0456,0x0457,0x0458,0x0459],
    # 武器 - 莉夏
    [0x0460,0x0461,0x0462,0x0463,0x0464],
    # 武器 - 达德利
    [0x0465,0x0466,0x0467,0x0468,0x0469],
    # 武器 - 亚里欧斯
    [0x046a],
    # 武器 - 赛特
    [0x046f,0x0474],
    # 装备 - 服装
    [0x0477,0x05dc,0x05dd,0x05de,0x05df,0x05e0,0x05e1,0x05e2,0x05e3,0x05e4,0x05e5,0x05e6,0x05e7,0x05e8,0x05e9,0x05ea,0x05eb,0x05ec,0x05ed,0x05ee,0x05ef,0x05f0,0x05f1,0x05f2,0x05f3,0x05f4,0x05f5,0x05f6,0x05f7,0x05f8,0x05f9,0x05fa,0x05fb,0x05fc],
    # 装备 - 鞋子
    [0x0478,0x0640,0x0641,0x0642,0x0643,0x0644,0x0645,0x0646,0x0647,0x0648,0x0649,0x064a,0x064b,0x064c,0x064d,0x064e,0x064f,0x0650,0x0651,0x0652,0x0653,0x0654,0x0655,0x0656,0x0657,0x0658,0x0659,0x065a],
    # 装备 - 饰品
    [0x001e,0x001f,0x0020,0x0021,0x0022,0x0023,0x0024,0x0025,0x0026,0x0027,0x0028,0x0029,0x002a,0x002b,0x002c,0x002d,0x002e,0x002f,0x0030,0x0031,0x0032,0x0033,0x0034,0x0035,0x0036,0x0037,0x0038,0x0039,0x003a,0x003c,0x003d,0x003e,0x003f,0x0040,0x0041,0x0042,0x0043,0x0044,0x0045,0x0046,0x0047,0x0048,0x0049,0x004a,0x004b,0x004c,0x004d,0x004e,0x004f,0x0050,0x0051,0x0052,0x0053,0x0054,0x0055,0x0056,0x0057,0x0058,0x0059,0x005a,0x005b,0x005c,0x005e,0x005f,0x0061,0x0063,0x0398,0x0399,0x039a,0x039b,0x039c,0x039d,0x039e,0x039f,0x03a0,0x03a1],
    # 回路 - 普通
    [0x0064,0x0065,0x0066,0x0067,0x0068,0x0069,0x006a,0x006b,0x006c,0x006d,0x006e,0x006f,0x0070,0x0071,0x0072,0x0073,0x0074,0x0075,0x0076,0x0077,0x0078,0x0079,0x007a,0x007b,0x007c,0x007d,0x007e,0x007f,0x0080,0x0081,0x0082,0x0083,0x0084,0x0085,0x0086,0x0088,0x0089,0x008a,0x008b,0x008c,0x008d,0x008e,0x008f,0x0090,0x0091,0x0092,0x0093,0x0094,0x0095,0x0096,0x0097,0x0098,0x0099,0x009a,0x009b,0x009c,0x009d,0x009e,0x009f,0x00a0,0x00a1,0x00a2,0x00a3,0x00a4,0x00a5,0x00a6,0x00a7,0x00a8,0x00a9,0x00aa,0x00ab,0x00ac,0x00ad,0x00ae,0x00af,0x00b0,0x00b1,0x00b2,0x00b3,0x00b4,0x00b5,0x00b6,0x00b7,0x00b8,0x00b9,0x00ba,0x00bb,0x00bc,0x00bd,0x00be,0x00bf,0x00c0,0x00c1,0x00c2,0x00c3,0x00c4,0x00c5,0x00c6],
    # 回路 - 核心
    [0x00dc,0x00dd,0x00de,0x00df,0x00e0,0x00e1,0x00e2,0x00e3,0x00e4,0x00e5,0x00e6,0x00e7,0x00e8,0x00e9,0x00ea,0x00eb,0x00ec,0x00ed,0x00ee,0x00ef,0x00f0,0x00f1],
    # 回路 - Debug
    [0x0087,0x00cb,0x00cc,0x00cd,0x00ce,0x00cf,0x00d0,0x00d1,0x00d2,0x00d3,0x00d4,0x00d5,0x00d6,0x00d7,0x00d8],
    # 事件 - 剧情
    [0x0320,0x0321,0x0322,0x0323,0x0324,0x0325,0x0326,0x0328,0x0329,0x032b,0x032c,0x032d,0x032e,0x032f,0x0330,0x0331,0x0332,0x0333,0x0334,0x0335,0x0336,0x0337,0x0338,0x0339,0x033a,0x033e,0x033f,0x0340,0x0341,0x0342,0x0343,0x0344,0x0345,0x0346,0x0347,0x035c,0x035d,0x035e,0x0375,0x0376,0x0377,0x0378,0x0379,0x038e,0x0394,0x0395,0x0396],
    # 事件 - 家具
    [0x0348,0x0349,0x034a,0x034b,0x034c,0x034d,0x034e,0x034f,0x0350,0x0351,0x0352,0x0353,0x0354,0x0355,0x0356,0x0357,0x0358],
    # 事件 - 导力车
    [0x035f,0x0360,0x0361,0x0362,0x0363,0x0364,0x0365,0x0366,0x0367,0x0368,0x0369,0x036a,0x036b,0x036c,0x036d,0x036e,0x036f,0x0370,0x0371,0x0372,0x0373,0x0374],
    # 食材
    [0x012c,0x012d,0x012e,0x012f,0x0130,0x0131,0x0132,0x0134,0x0135,0x0136,0x0137,0x0138,0x0139,0x013a,0x013b,0x013c,0x013d,0x013e,0x013f,0x0140,0x0141,0x0142,0x0143,0x0144,0x0145,0x0146,0x0147,0x0148,0x0149,0x014a],
    # 书籍
    [0x0001,0x0002,0x0003,0x0004,0x0005,0x0006,0x000a,0x000b,0x000c,0x000d,0x000e,0x000f,0x0010,0x0011,0x02bc,0x02bd,0x02be,0x02bf,0x02c0,0x02c1,0x02c2,0x02c3,0x02c4,0x02c6,0x02c7,0x02c8,0x02c9,0x02ca,0x02cb,0x02cc,0x02cd,0x02ce,0x02cf,0x02d0,0x02d1,0x02d2,0x02d3,0x02d5,0x02d6,0x02d7,0x02d8,0x02d9,0x02da,0x02dd,0x02de,0x02df,0x02e0,0x02e1,0x02e2,0x02e3,0x02e4,0x02e5,0x02e6,0x02e7,0x02e8,0x02e9,0x02ea,0x02eb,0x02ec,0x02ee,0x02ef,0x02f0,0x02f1,0x02f2,0x02f3,0x02f4,0x02f5,0x02f6,0x02f7,0x02f8,0x02f9,0x02fa,0x02fb,0x02fc],
    # 垂钓 - 鱼饵
    [0x0186,0x0187,0x0188,0x0189,0x018a,0x018b,0x018c],
    # 垂钓 - 鱼
    [0x015e,0x015f,0x0160,0x0161,0x0162,0x0163,0x0164,0x0165,0x0166,0x0167,0x0168,0x0169,0x016a,0x016b,0x016c,0x016d,0x016e,0x016f,0x0170,0x0171,0x0172,0x0173,0x0174,0x0175,0x0176,0x0177,0x0178,0x0179,0x017a,0x017b,0x017c],
    # 垂钓 - 钓竿
    [0x0014,0x0015,0x0016,0x0017,0x0018],
]

def item_name(code, lang="zh_cn"):
    """获取当前语言下的物品名称，缺失时回退到中文名。"""
    zh_name = ITEM_DB.get(code, ("", f"未知(0x{code:04x})"))[1]
    if lang == "zh_cn":
        return zh_name
    localized = ITEM_I18N.get(code, {}).get(lang)
    return localized or zh_name


def item_search_text(code):
    names = [ITEM_DB.get(code, ("", ""))[1]]
    i18n = ITEM_I18N.get(code, {})
    names.extend([i18n.get("en", ""), i18n.get("ja", "")])
    names.append(f"0x{code:04x}")
    return " ".join(name for name in names if name).lower()


def achievement_name(part, bit, zh_name, lang="zh_cn"):
    if lang == "zh_cn":
        return zh_name
    localized = ACHIEVEMENT_I18N.get((part, bit), {}).get(lang)
    return localized or zh_name


def ui_text(text, lang="zh_cn"):
    translated = UI_TRANSLATIONS.get(lang, {}).get(text)
    if translated is not None:
        return translated
    if text in CHARACTER_NAME_I18N:
        return character_name(text, lang)
    return UI_TRANSLATIONS["zh_cn"].get(text, text)

ITEM_ORDERED_CODES = tuple(code for cat_codes in ITEM_WRITE_ORDER for code in cat_codes)
ITEM_ORDERED_SET = set(ITEM_ORDERED_CODES)

def item_codes_for_categories(*categories):
    """按 BZH 写入顺序返回指定类别的物品代码。"""
    wanted = set(categories)
    return [
        code for code in ITEM_ORDERED_CODES
        if ITEM_DB.get(code, ("", ""))[0] in wanted
    ]

def item_codes_by_prefix(*prefixes):
    """按 BZH 写入顺序返回类别前缀匹配的物品代码。"""
    return [
        code for code in ITEM_ORDERED_CODES
        if ITEM_DB.get(code, ("", ""))[0].startswith(prefixes)
    ]

# ============================================================
# P0: 成就系统 (7 bytes 位图)
# ============================================================
ACHIEVEMENT_OFFSETS = [0x000004C4 + i for i in range(7)]

ACHIEVEMENT_NAMES = [
    # (part_index, bit, chinese_name)
    (0, 0, "三星厨师"), (0, 1, "爆钓王"), (0, 2, "宝箱猎人"),
    (0, 3, "小说爱好者"), (0, 4, "回路收藏家"), (0, 5, "炎之料理人"),
    (0, 6, "天眼的智者"), (0, 7, "市民的英雄"),
    (1, 0, "千战之志士"), (1, 1, "历战之胜者"), (1, 2, "奋战之猛士"),
    (1, 3, "力战之勇士"), (1, 4, "百万富翁"), (1, 5, "组合技大师"),
    (1, 6, "D之追及者"), (1, 7, "不拘一格的厨师"),
    (2, 0, "导力车发烧友"), (2, 1, "家具收藏家"), (2, 2, "无双之猎士"),
    (2, 3, "最强之剑"), (2, 4, "超一流搜查官"), (2, 5, "持续的压迫"),
    (2, 6, "超绝秘技"), (2, 7, "雷光一闪"),
    (3, 0, "短暂的休息"), (3, 1, "西塞姆利亚通商会议"),
    (3, 2, "预兆~新的生活"), (3, 3, "D之残影"),
    (3, 4, "传说的搜查官"), (3, 5, "干练的搜查官"),
    (3, 6, "艾尼格玛Ⅱ用户"), (3, 7, "至境之珠"),
    (4, 0, "与莉夏的羁绊"), (4, 1, "与瓦吉的羁绊"),
    (4, 2, "与诺艾尔的羁绊"), (4, 3, "与达德利的羁绊"),
    (4, 4, "即便如此我们也…"), (4, 5, "跨越虚幻的乐园"),
    (4, 6, "命运未卜的克洛斯贝尔"), (4, 7, "胎动～众兽的狂欢节"),
    (5, 0, "连战连胜"), (5, 1, "绚烂攻击"), (5, 2, "百花迎击"),
    (5, 3, "刚之追随者"), (5, 4, "红之讨伐者"),
    (5, 5, "与兰迪的羁绊"), (5, 6, "与缇欧的羁绊"),
    (5, 7, "与艾莉的羁绊"),
    (6, 0, "绮耀之贤士"), (6, 1, "怪物射击大师"),
    (6, 2, "波波碰大师"), (6, 3, "传承的思念～不断的羁绊"),
    (6, 4, "解明真相者"), (6, 5, "爆裂果敢"),
    (6, 6, "赶紧杀绝"), (6, 7, "霸头歼灭"),
]

# ============================================================
# P0: 战斗手册 (12 counters, u16)
# ============================================================
BATTLE_STATS = {
    "战斗次数":       0x0001F378,
    "失败次数":       0x0001F37A,
    "胜利次数":       0x0001F37C,
    "逃跑次数":       0x0001F380,
    "重试战斗次数":    0x0001F382,
    "S战技使用次数":   0x0001F384,
    "组合战技次数":    0x0001F386,
    "先制攻击次数":    0x0001F388,
    "被偷袭次数":      0x0001F38A,
    "杀敌数":         0x0001F38C,
    "爆灵次数":       0x0001F38E,
}

# ============================================================
# P1: 角色显示外观 (12 slots, u16)
# ============================================================
ROLE_DISPLAY_OFFSETS = [0x0001B358 + i * 2 for i in range(12)]

ROLE_DISPLAY_NAMES = {  # ID -> 名称
    0: "罗伊德", 1: "艾莉", 2: "缇欧", 3: "兰迪",
    4: "瓦吉(初期)", 5: "瓦吉(后期)", 6: "银", 7: "莉夏",
    8: "蔡特", 9: "亚里欧斯", 10: "诺艾尔", 11: "达德利",
    12: "加尔西亚", 13: "魔兽(跳跳猫)",
    14: "亚里欧斯(NPC)", 15: "罗伊德(NPC1)",
    16: "罗伊德(NPC2)", 17: "雷蒙德", 18: "秦",
    19: "谢莉", 20: "琪雅",
}

ROLE_DISPLAY_I18N = {
    0: {"en": "Lloyd", "ja": "ロイド"},
    1: {"en": "Elie", "ja": "エリィ"},
    2: {"en": "Tio", "ja": "ティオ"},
    3: {"en": "Randy", "ja": "ランディ"},
    4: {"en": "Wazy (Early)", "ja": "ワジ(初期)"},
    5: {"en": "Wazy (Late)", "ja": "ワジ(後期)"},
    6: {"en": "Silver", "ja": "銀"},
    7: {"en": "Rixia", "ja": "リーシャ"},
    8: {"en": "Zeit", "ja": "ツァイト"},
    9: {"en": "Arios", "ja": "アリオス"},
    10: {"en": "Noel", "ja": "ノエル"},
    11: {"en": "Dudley", "ja": "ダドリー"},
    12: {"en": "Garcia", "ja": "ガルシア"},
    13: {"en": "Flying Feline", "ja": "魔獣(跳ね猫)"},
    14: {"en": "Arios (NPC)", "ja": "アリオス(NPC)"},
    15: {"en": "Lloyd (NPC1)", "ja": "ロイド(NPC1)"},
    16: {"en": "Lloyd (NPC2)", "ja": "ロイド(NPC2)"},
    17: {"en": "Raymond", "ja": "レイモンド"},
    18: {"en": "Xin", "ja": "シン"},
    19: {"en": "Shirley", "ja": "シズク"},
    20: {"en": "KeA", "ja": "キーア"},
}


def role_display_name(role_id, lang="zh_cn"):
    if lang == "zh_cn":
        return ROLE_DISPLAY_NAMES.get(role_id, f"未知({role_id})")
    return ROLE_DISPLAY_I18N.get(role_id, {}).get(lang) or ROLE_DISPLAY_NAMES.get(role_id, f"未知({role_id})")

# ============================================================
# P1: 怪物图鉴 (variable-length records)
# ============================================================
MONSTER_START = 0x0001B370
MONSTER_END   = 0x0001BCF0

# 来自 bzh_ank_se_code_define_manual.h 的真实怪物代码列表。存档记录必须写这些
# u32 code；写顺序号会让游戏/原工具无法识别已解锁怪物。
MONSTER_CODES = (
    0x30072200, 0x30086200, 0x30083600, 0x30083800, 0x30084600, 0x30083900, 0x30071800, 0x30082900,
    0x30080700, 0x30067400, 0x30088000, 0x30002102, 0x30069001, 0x30062001, 0x30075900, 0x30064900,
    0x30060900, 0x30074800, 0x30063200, 0x30070300, 0x30070400, 0x30070500, 0x30071300, 0x30064200,
    0x30071500, 0x30071900, 0x30066403, 0x30066900, 0x30065100, 0x30080801, 0x30060701, 0x30072400,
    0x30072401, 0x30078900, 0x30084700, 0x30081600, 0x30078600, 0x30083000, 0x30078700, 0x30081101,
    0x30063100, 0x30062500, 0x30065500, 0x30065900, 0x30069400, 0x30077400, 0x30064400, 0x30083200,
    0x30066402, 0x30076100, 0x30064300, 0x30066300, 0x30041900, 0x30003400, 0x30042100, 0x30076001,
    0x30068100, 0x30072800, 0x30069100, 0x30071700, 0x30079501, 0x30083400, 0x30078100, 0x30078300,
    0x30079400, 0x30079500, 0x30067000, 0x30088100, 0x30068600, 0x30087600, 0x30066500, 0x30069900,
    0x30063000, 0x30061000, 0x30064000, 0x30066200, 0x30066400, 0x30066700, 0x30069300, 0x30042500,
    0x30024100, 0x30063700, 0x30063701, 0x30088700, 0x30088800, 0x30068800, 0x30074201, 0x30062200,
    0x30062600, 0x30063900, 0x30064500, 0x30069800, 0x30061800, 0x30066801, 0x30068900, 0x30076201,
    0x30072201, 0x30062100, 0x30066600, 0x30063600, 0x30065800, 0x30065200, 0x30061300, 0x30065300,
    0x30069700, 0x30065700, 0x30061100, 0x30070800, 0x30061400, 0x30070700, 0x30065600, 0x30072300,
    0x30062400, 0x30072700, 0x30068500, 0x30066401, 0x30062300, 0x30070201, 0x30070200, 0x30070000,
    0x30088900, 0x30088901, 0x30088702, 0x30088802, 0x30081001, 0x30031200, 0x30031300, 0x30044900,
    0x30082004, 0x30032000, 0x30032100, 0x30032001, 0x30032101, 0x30063800, 0x30068700, 0x30075800,
    0x30060500, 0x30073200, 0x30073400, 0x30074300, 0x30074400, 0x30074500, 0x30074600, 0x30075100,
    0x30073600, 0x30073700, 0x30074000, 0x30073000, 0x30074700, 0x30073500, 0x30080300, 0x30080200,
    0x30080600, 0x30003600, 0x30084101, 0x30084201, 0x30084301, 0x30084100, 0x30084200, 0x30084300,
    0x30081800, 0x30042200, 0x30042300, 0x30088600, 0x30066100, 0x30080100, 0x30087000, 0x30087100,
    0x30087200, 0x30087300, 0x30087400, 0x30087500, 0x30084400, 0x30085900, 0x30086600, 0x30088401,
    0x30088701, 0x30088801, 0x30088101, 0x30078400, 0x30082400, 0x30082800, 0x30086700, 0x30078001,
    0x30088300, 0x30078200, 0x30082700, 0x30083300, 0x30086800, 0x30088400, 0x30087800, 0x30089200,
    0x30086900, 0x30082500, 0x30083700, 0x30082000, 0x30003300, 0x30069500, 0x30063400, 0x30063500,
    0x30066800, 0x30064100, 0x30071600, 0x30075600, 0x30067200, 0x30041901, 0x30042000, 0x30082001,
    0x30061500, 0x30084800, 0x30079000, 0x30084900, 0x30079101, 0x30088200, 0x30081201, 0x30082100,
    0x30082200, 0x30082300, 0x30079600, 0x30079700, 0x30079800, 0x30003800, 0x30041400, 0x30041500,
    0x30080800, 0x30041401, 0x30041501, 0x30003900, 0x30041902, 0x30042001, 0x30082002, 0x30086100,
    0x30042002, 0x30084000, 0x30084500, 0x30080000, 0x30063300, 0x30064600, 0x30062800, 0x30065000,
    0x30062700, 0x30075200, 0x30043200, 0x30043300, 0x30043100, 0x30043101, 0x30003500, 0x30004200,
    0x30085100, 0x30082600, 0x30085101, 0x30079100, 0x30079200, 0x30079300, 0x30088500, 0x30085300,
    0x30080900, 0x30085000, 0x30074200, 0x30079900, 0x30085200, 0x30089300, 0x30078800, 0x30087700,
    0x30082003, 0x30081000, 0x30003401, 0x30078000, 0x30081400, 0x30085800, 0x30080400, 0x30081401,
    0x30088301, 0x30085400, 0x30081100, 0x30087900, 0x30085700, 0x30085201, 0x30089301, 0x30085600,
    0x30081700, 0x30081900, 0x30086101, 0x30081200, 0x30003301, 0x30085500, 0x30071801, 0x30083500,
    0x30070100, 0x30081500, 0x30085202, 0x30089302, 0x30081300, 0x30079301, 0x30085301, 0x30078500,
    0x30085401, 0x30085501, 0x30002401, 0x30080500, 0x30003700, 0x30086500, 0x30086400, 0x30089000,
    0x30089100,
)

TEAM_NAMES = {
    0: "罗伊德", 1: "艾莉", 2: "缇欧", 3: "兰迪",
    4: "瓦吉", 5: "莉夏", 6: "赛特", 7: "亚里欧斯",
    8: "诺艾尔", 9: "达德利", 10: "加尔西亚",
    255: "(空)"
}

DIFFICULTY_NAMES = {0: "Easy", 1: "Normal", 2: "Hard", 3: "Nightmare"}

# ============================================================
# 存档读写核心
# ============================================================

class SaveData:
    def __init__(self):
        self.data = None
        self.filepath = None
        self.tempfile = None

    def load(self, filepath):
        """加载 zstd 压缩或已解压的 savedata.dat。"""
        self.filepath = filepath
        with open(filepath, "rb") as f:
            raw = f.read()

        if raw[:4] == b"\x28\xb5\x2f\xfd":
            if zstd is None:
                raise RuntimeError("缺少 zstandard 依赖，无法读取压缩存档。请先安装: pip install zstandard") from ZSTD_IMPORT_ERROR
            dctx = zstd.ZstdDecompressor()
            try:
                data = dctx.decompress(raw, max_output_size=EXPECTED_SIZE + 0x1000)
            except zstd.ZstdError:
                return False
        else:
            data = raw

        if len(data) < EXPECTED_SIZE:
            return False
        self.data = bytearray(data[:EXPECTED_SIZE])
        return True

    def save(self, filepath=None):
        """保存为 zstd 压缩格式。"""
        if filepath is None:
            filepath = self.filepath
        if not filepath:
            raise ValueError("未指定保存路径")
        if self.data is None:
            raise ValueError("未加载存档")
        if zstd is None:
            raise RuntimeError("缺少 zstandard 依赖，无法保存压缩存档。请先安装: pip install zstandard") from ZSTD_IMPORT_ERROR
        if len(self.data) != EXPECTED_SIZE:
            raise ValueError(f"存档大小异常: {len(self.data)} bytes，期望 {EXPECTED_SIZE} bytes")

        self._recalc_checksum()
        cctx = zstd.ZstdCompressor(level=3)
        compressed = cctx.compress(bytes(self.data))
        bak = filepath + ".bak"
        if os.path.exists(filepath):
            os.replace(filepath, bak)
        with open(filepath, "wb") as f:
            f.write(compressed)
        return True

    def _recalc_checksum(self):
        """重新计算存档校验和 (BZH 算法：32位累加和)
        算法 (来自 bzh_ank_se_savedata_checksum.h):
          file_savedata_checksum = sum of all 32-bit values from 0 to (len-8)
          file_size_checksum = -((len-1-8)/4 + 1) - file_savedata_checksum (mod 2^32)
        同时校验文件大小：0x0002643b (因为 size() == 0x2643b = 0x2643c-1)
        """
        file_size_max_pos = len(self.data) - 1

        # 1. file_savedata_checksum: 累加所有 32-bit 数值
        savedata_sum = 0
        pos = 0
        while pos <= (file_size_max_pos - 0x08):
            cache = struct.unpack_from('<I', self.data, pos)[0]
            savedata_sum = (savedata_sum + cache) & 0xFFFFFFFF
            pos += 0x04

        # 2. file_size_checksum
        num_chunks = ((file_size_max_pos - 0x08) // 0x04) + 0x01
        size_checksum = (-1 * num_chunks) & 0xFFFFFFFF
        size_checksum = (size_checksum - savedata_sum) & 0xFFFFFFFF

        # 写入两个校验和
        struct.pack_into('<I', self.data, CHECKSUM_USER, savedata_sum)
        struct.pack_into('<I', self.data, CHECKSUM_USER_SIZE, size_checksum)

    def read_u32(self, offset):
        return struct.unpack_from("<I", self.data, offset)[0]

    def read_u16(self, offset):
        return struct.unpack_from("<H", self.data, offset)[0]

    def read_u8(self, offset):
        return self.data[offset]

    def write_u32(self, offset, val):
        struct.pack_into("<I", self.data, offset, val & 0xFFFFFFFF)

    def write_u16(self, offset, val):
        struct.pack_into("<H", self.data, offset, val & 0xFFFF)

    def write_u8(self, offset, val):
        self.data[offset] = val & 0xFF

    def read_items(self):
        """读取物品列表 → {code: qty}"""
        items = {}
        pos = ITEMS_START
        while pos <= ITEMS_END:
            code = self.read_u16(pos)
            qty = self.read_u16(pos + 2)
            if code != 0:
                items[code] = qty
            pos += 4
        return items

    def write_items(self, items):
        """按 BZH 顺序写入物品列表，保留未知代码并检查容量。"""
        entries = []
        for code in ITEM_ORDERED_CODES:
            qty = int(items.get(code, 0) or 0)
            if qty > 0:
                entries.append((code, qty))

        for code in sorted(set(items) - ITEM_ORDERED_SET):
            qty = int(items.get(code, 0) or 0)
            if code and qty > 0:
                entries.append((code, qty))

        capacity = ((ITEMS_END - ITEMS_START) // 4) + 1
        if len(entries) > capacity:
            raise ValueError(f"物品数量超出存档容量: {len(entries)} > {capacity}")

        pos = ITEMS_START
        for code, qty in entries:
            self.write_u16(pos, code)
            self.write_u16(pos + 2, qty)
            pos += 4

        while pos <= ITEMS_END:
            self.write_u16(pos, 0)
            self.write_u16(pos + 2, 0)
            pos += 4

    def read_achievements(self):
        """读取成就位图 → {part_index: bits_list}"""
        bits = {}
        for i, off in enumerate(ACHIEVEMENT_OFFSETS):
            byte_val = self.read_u8(off)
            bits[i] = [(byte_val >> b) & 1 for b in range(8)]
        return bits

    def write_achievements(self, bits):
        """写入成就位图"""
        for i, off in enumerate(ACHIEVEMENT_OFFSETS):
            byte_val = 0
            for b in range(8):
                if bits.get(i, [0]*8)[b]:
                    byte_val |= (1 << b)
            self.write_u8(off, byte_val)

    def unlock_all_monsters(self):
        """按 BZH 怪物代码一键解锁全部怪物图鉴。"""
        pos = MONSTER_START
        for code in MONSTER_CODES:
            if pos > MONSTER_END:
                raise ValueError("怪物图鉴记录超出存档容量")
            self.write_u32(pos, code)
            self.write_u8(pos + 4, 0x08)       # flag: BZH 写入已登记记录时使用 0x08
            self.write_u8(pos + 5, 0xFE)       # resistance: 地/水/火/风/时/空/幻全开，道具位另存
            self.write_u8(pos + 6, 0xFF)       # stats/description/sepith/resistance 等全开
            self.write_u8(pos + 7, 0xFF)       # get_item
            pos += 8

        while pos <= MONSTER_END:
            self.write_u32(pos, 0)
            self.write_u32(pos + 4, 0)
            pos += 8


# ============================================================
# GUI
# ============================================================

class SaveEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("碧之轨迹 NISA版 存档修改器")
        self.geometry("820x680")
        self.resizable(True, True)
        self.save = SaveData()
        self._vars = {}  # StringVar 缓存
        self._build_ui()

    def _build_ui(self):
        # 工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=5)

        self._toolbar_open_btn = ttk.Button(toolbar, text="打开存档 (savedata.dat)", command=self._open_file)
        self._toolbar_open_btn.pack(side="left", padx=3)
        self._toolbar_save_btn = ttk.Button(toolbar, text="保存存档", command=self._save_file)
        self._toolbar_save_btn.pack(side="left", padx=3)
        self._ui_lang_label = ttk.Label(toolbar, text="语言")
        self._ui_lang_label.pack(side="left", padx=(16, 2))
        self._ui_lang_var = tk.StringVar(value="zh_cn:中文")
        self._ui_lang_combo = ttk.Combobox(
            toolbar,
            textvariable=self._ui_lang_var,
            values=[f"{key}:{label}" for key, label in ITEM_LANGUAGE_LABELS.items()],
            width=12,
            state="readonly",
        )
        self._ui_lang_combo.pack(side="left", padx=2)
        self._ui_lang_combo.bind("<<ComboboxSelected>>", self._on_ui_language_changed)
        self.status_lbl = ttk.Label(toolbar, text="未加载存档")
        self.status_lbl.pack(side="left", padx=20)
        self._status_key = "未加载存档"
        self._status_kwargs = {}

        # Notebook 标签页
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=5, pady=5)
        self._tab_defs = []

        # 标签1: 基本
        frm_basic = ttk.Frame(self._nb)
        self._nb.add(frm_basic, text="基本 / Mira")
        self._tab_defs.append((frm_basic, "基本 / Mira"))
        self._build_basic_tab(frm_basic)

        # 标签2: 角色
        frm_char = ttk.Frame(self._nb)
        self._nb.add(frm_char, text="角色属性")
        self._tab_defs.append((frm_char, "角色属性"))
        self._build_char_tab(frm_char)

        # 标签3: 队伍 & 好感
        frm_team = ttk.Frame(self._nb)
        self._nb.add(frm_team, text="队伍 / 好感度")
        self._tab_defs.append((frm_team, "队伍 / 好感度"))
        self._build_team_tab(frm_team)

        # 标签4: 物品
        frm_items = ttk.Frame(self._nb)
        self._nb.add(frm_items, text="物品")
        self._tab_defs.append((frm_items, "物品"))
        self._build_items_tab(frm_items)

        # 标签5: 成就
        frm_ach = ttk.Frame(self._nb)
        self._nb.add(frm_ach, text="成就")
        self._tab_defs.append((frm_ach, "成就"))
        self._build_achievement_tab(frm_ach)

        # 标签6: 战斗手册
        frm_btl = ttk.Frame(self._nb)
        self._nb.add(frm_btl, text="战斗手册")
        self._tab_defs.append((frm_btl, "战斗手册"))
        self._build_battle_tab(frm_btl)

        # 标签7: 外观
        frm_app = ttk.Frame(self._nb)
        self._nb.add(frm_app, text="角色外观")
        self._tab_defs.append((frm_app, "角色外观"))
        self._build_appearance_tab(frm_app)

        # 标签8: 快捷操作
        frm_quick = ttk.Frame(self._nb)
        self._nb.add(frm_quick, text="快捷操作")
        self._tab_defs.append((frm_quick, "快捷操作"))
        self._build_quick_tab(frm_quick)

        self._register_localizable_widgets(self)
        self._apply_ui_language(initial=True)

    def _var(self, name):
        if name not in self._vars:
            self._vars[name] = tk.StringVar()
        return self._vars[name]

    def _lb_entry(self, parent, label, var_name, row, col, width=10):
        ttk.Label(parent, text=label).grid(row=row, column=col*2, sticky="e", padx=2, pady=1)
        e = ttk.Entry(parent, textvariable=self._var(var_name), width=width)
        e.grid(row=row, column=col*2+1, sticky="w", padx=2, pady=1)
        return e

    def _current_ui_language(self):
        value = self._ui_lang_var.get() if hasattr(self, "_ui_lang_var") else "zh_cn"
        return value.split(":", 1)[0]

    def _on_ui_language_changed(self, _event=None):
        self._apply_ui_language()

    def _t(self, text, **kwargs):
        msg = ui_text(text, self._current_ui_language())
        return msg.format(**kwargs) if kwargs else msg

    def _set_status(self, text, **kwargs):
        self._status_key = text
        self._status_kwargs = kwargs
        self.status_lbl.config(text=self._t(text, **kwargs))

    def _render_status(self):
        key = getattr(self, "_status_key", "未加载存档")
        kwargs = getattr(self, "_status_kwargs", {})
        self.status_lbl.config(text=self._t(key, **kwargs))

    def _register_localizable_widgets(self, widget):
        try:
            current = widget.cget("text")
        except Exception:
            current = None
        if isinstance(current, str) and current and not hasattr(widget, "_ui_base_text"):
            widget._ui_base_text = current
        try:
            children = widget.winfo_children()
        except Exception:
            children = []
        for child in children:
            self._register_localizable_widgets(child)

    def _apply_ui_language(self, initial=False):
        lang = self._current_ui_language()
        self.title(APP_TITLES.get(lang, APP_TITLES["zh_cn"]))
        if hasattr(self, "_ui_lang_var"):
            self._ui_lang_var.set({"zh_cn": "zh_cn:中文", "en": "en:English", "ja": "ja:日本語"}.get(lang, "zh_cn:中文"))
        if hasattr(self, "_ui_lang_label"):
            self._ui_lang_label.config(text=self._t("语言"))
        if hasattr(self, "_toolbar_open_btn"):
            self._toolbar_open_btn.config(text=self._t("打开存档 (savedata.dat)"))
        if hasattr(self, "_toolbar_save_btn"):
            self._toolbar_save_btn.config(text=self._t("保存存档"))
        if hasattr(self, "status_lbl") and not initial:
            self._render_status()
        if hasattr(self, "_tab_defs"):
            for frame, key in self._tab_defs:
                self._nb.tab(frame, text=self._t(key))
        for widget in self.winfo_children():
            self._translate_widget_tree(widget, lang)
        if hasattr(self, "_tree"):
            self._tree.heading("code", text=self._t("代码"))
            self._tree.heading("name", text=self._t("名称"))
            self._tree.heading("qty", text=self._t("数量"))
            self._refresh_items_ui()
        if hasattr(self, "_appearance_vars"):
            self._refresh_appearance_ui()
        if hasattr(self, "_battle_vars"):
            self._refresh_battle_ui()
        if hasattr(self, "_ach_vars"):
            self._refresh_achievements_ui()
        self.update_idletasks()

    def _translate_widget_tree(self, widget, lang):
        base = getattr(widget, "_ui_base_text", None)
        if base and widget is not getattr(self, "status_lbl", None):
            try:
                widget.config(text=ui_text(base, lang))
            except Exception:
                pass
        try:
            children = widget.winfo_children()
        except Exception:
            children = []
        for child in children:
            self._translate_widget_tree(child, lang)

    def _build_basic_tab(self, frm):
        frm.grid_columnconfigure(0, weight=1)
        frm.grid_columnconfigure(2, weight=1)

        f1 = ttk.LabelFrame(frm, text=self._t("资源"))
        f1.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        self._lb_entry(f1, "Mira", "mira", 0, 0)
        self._lb_entry(f1, "DP", "dp", 1, 0)
        self._lb_entry(f1, "Medal", "medal", 2, 0)

        f2 = ttk.LabelFrame(frm, text=self._t("耀晶片"))
        f2.grid(row=0, column=1, sticky="nw", padx=5, pady=5)
        for i, name in enumerate(["地","水","火","风","时","空","幻"]):
            self._lb_entry(f2, self._t(name), f"sepith_{name}", i, 0)

        f3 = ttk.LabelFrame(frm, text=self._t("游戏时间"))
        f3.grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        self._lb_entry(f3, "总秒数", "time_s", 0, 0)
        self._lb_entry(f3, "时", "time_h", 1, 0)
        self._lb_entry(f3, "分", "time_m", 2, 0)
        self._lb_entry(f3, "秒", "time_sec", 3, 0)

        f4 = ttk.LabelFrame(frm, text=self._t("难度 (0=Easy 1=Normal 2=Hard 3=Nightmare)"))
        f4.grid(row=1, column=1, sticky="nw", padx=5, pady=5)
        self._lb_entry(f4, self._t("难度"), "difficulty", 0, 0, width=4)

    def _build_char_tab(self, frm):
        canvas = tk.Canvas(frm)
        scrollbar = ttk.Scrollbar(frm, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        attrs = ["max_hp","hp","lv","max_ep","ep","cp","exp","str","def","ats","adf"]
        attr_cn = {"max_hp":"最大HP","hp":"当前HP","lv":"等级","max_ep":"最大EP","ep":"当前EP",
                   "cp":"CP","exp":"EXP","str":"STR","def":"DEF","ats":"ATS","adf":"ADF"}

        # 表头
        ttk.Label(scrollable, text=self._t("角色"), width=8).grid(row=0, column=0, sticky="w")
        for j, a in enumerate(attrs):
            ttk.Label(scrollable, text=self._t(attr_cn[a]), width=8).grid(row=0, column=j+1)

        for i, (name, base) in enumerate(CHAR_BASES.items()):
            ttk.Label(scrollable, text=character_name(name, self._current_ui_language()), font=("", 9, "bold")).grid(row=i+1, column=0, sticky="w")
            for j, attr in enumerate(attrs):
                vn = f"char_{name}_{attr}"
                offset = base + CHAR_ATTR[attr]
                if attr in ("max_hp","hp","exp"):
                    w = 9
                elif attr == "lv":
                    w = 4
                else:
                    w = 6
                e = ttk.Entry(scrollable, textvariable=self._var(vn), width=w)
                e.grid(row=i+1, column=j+1, padx=1)
                e.bind("<FocusOut>", lambda ev, o=offset, vt="u32": self._on_char_edit(o, vt, ev))
                # 悬停提示偏移量
                tk.ToolTip = None  # skip; just show offset in status

    def _build_team_tab(self, frm):
        f1 = ttk.LabelFrame(frm, text=self._t("队伍编成 (0=罗伊德, 1=艾莉, ..., 255=空)"))
        f1.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        for i in range(8):
            self._lb_entry(f1, self._t("队员 {num}", num=i+1), f"team_{i}", i, 0, width=5)

        f2 = ttk.LabelFrame(frm, text=self._t("好感度 (0-? )"))
        f2.grid(row=0, column=1, sticky="nw", padx=5, pady=5)
        for i, (name, off) in enumerate(LIKEABILITY.items()):
            self._lb_entry(f2, character_name(name, self._current_ui_language()), f"like_{name}", i, 0, width=5)

    def _build_items_tab(self, frm):
        frm.grid_columnconfigure(0, weight=1)
        frm.grid_rowconfigure(1, weight=1)

        # 搜索栏
        bar = ttk.Frame(frm)
        bar.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        ttk.Label(bar, text=self._t("搜索:")).pack(side="left")
        self._search_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self._search_var, width=20).pack(side="left", padx=5)
        ttk.Button(bar, text=self._t("过滤"), command=self._filter_items).pack(side="left", padx=2)
        ttk.Button(bar, text=self._t("全部显示"), command=self._refresh_items).pack(side="left", padx=2)
        ttk.Button(bar, text=self._t("选中 → 99"), command=self._items_set_selected).pack(side="right", padx=2)
        ttk.Button(bar, text=self._t("选中 → 0"), command=lambda: self._items_set_selected(0)).pack(side="right", padx=2)

        # Treeview
        cols = ("code", "name", "qty")
        self._tree = ttk.Treeview(frm, columns=cols, show="headings", selectmode="extended")
        self._tree.heading("code", text=self._t("代码"))
        self._tree.heading("name", text=self._t("名称"))
        self._tree.heading("qty", text=self._t("数量"))
        self._tree.column("code", width=70)
        self._tree.column("name", width=350)
        self._tree.column("qty", width=60)
        self._tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
        self._update_item_name_heading()

        scrollbar = ttk.Scrollbar(frm, orient="vertical", command=self._tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._items_data = {}  # code -> qty

    def _current_item_language(self):
        return self._current_ui_language()

    def _update_item_name_heading(self):
        if hasattr(self, "_tree"):
            self._tree.heading("name", text=self._t("名称"))

    def _on_item_language_changed(self, _event=None):
        self._update_item_name_heading()
        self._refresh_items_ui()

    def _refresh_items(self):
        self._items_data = self.save.read_items()
        self._search_var.set("")
        self._refresh_items_ui()

    def _refresh_items_ui(self):
        self._tree.delete(*self._tree.get_children())
        if self.save.data is None:
            return
        lang = self._current_item_language()
        for code, qty in sorted(self._items_data.items()):
            name = item_name(code, lang)
            self._tree.insert("", "end", values=(f"0x{code:04x}", name, qty))

    def _filter_items(self):
        keyword = self._search_var.get().lower().strip()
        self._tree.delete(*self._tree.get_children())
        if self.save.data is None:
            return
        self._items_data = self.save.read_items()
        lang = self._current_item_language()
        for code, qty in sorted(self._items_data.items()):
            name = item_name(code, lang)
            if not keyword or keyword in item_search_text(code):
                self._tree.insert("", "end", values=(f"0x{code:04x}", name, qty))

    def _items_set_selected(self, val=99):
        if self.save.data is None:
            return
        if not self._items_data:
            self._items_data = self.save.read_items()
        for iid in self._tree.selection():
            vals = self._tree.item(iid, "values")
            code = int(vals[0], 16)
            self._items_data[code] = val
            self._tree.item(iid, values=(vals[0], vals[1], val))
        self.save.write_items(self._items_data)

    def _write_items_from_gui(self):
        # 同步 Treeview 中的修改
        for iid in self._tree.get_children():
            vals = self._tree.item(iid, "values")
            code = int(vals[0], 16)
            qty = int(vals[2])
            self._items_data[code] = qty
        self.save.write_items(self._items_data)

    def _build_quick_tab(self, frm):
        frm.grid_columnconfigure(0, weight=1)

        ttk.Label(frm, text=self._t("一键操作 (先打开存档!)"), font=("", 12, "bold")).pack(pady=10)

        f1 = ttk.LabelFrame(frm, text=self._t("Max 资源"))
        f1.pack(padx=10, pady=5, fill="x")
        ttk.Button(f1, text=self._t("Mira → 9,999,999"), command=lambda: self._quick_set("mira", 9999999)).pack(side="left", padx=5, pady=5)
        ttk.Button(f1, text=self._t("全耀晶片 → 9,999"), command=self._quick_max_sepith).pack(side="left", padx=5, pady=5)
        ttk.Button(f1, text=self._t("DP → 400"), command=lambda: self._quick_set("dp", 400)).pack(side="left", padx=5, pady=5)

        f2 = ttk.LabelFrame(frm, text=self._t("Max 队伍角色"))
        f2.pack(padx=10, pady=5, fill="x")
        for name in CHAR_BASES.keys():
            ttk.Button(f2, text=self._t("{name} LV99 满HP/EP/CP", name=character_name(name, self._current_ui_language())),
                       command=lambda n=name: self._quick_max_char(n)).pack(side="left", padx=2, pady=2)

        f3 = ttk.LabelFrame(frm, text=self._t("好感度一键满"))
        f3.pack(padx=10, pady=5, fill="x")
        ttk.Button(f3, text=self._t("全员好感度 → 255"), command=self._quick_max_like).pack(side="left", padx=5, pady=5)

        f_items = ttk.LabelFrame(frm, text=self._t("Max 物品"))
        f_items.pack(padx=10, pady=5, fill="x")
        ttk.Button(f_items, text=self._t("全消耗品/食材/书籍 → 99"), command=self._quick_max_consumables).pack(side="left", padx=5, pady=5)
        ttk.Button(f_items, text=self._t("全回路 → 99 (含核心回路)"), command=self._quick_max_circuits).pack(side="left", padx=5, pady=5)
        ttk.Button(f_items, text=self._t("全装备 → 1"), command=self._quick_max_equipment).pack(side="left", padx=5, pady=5)

        f_monster = ttk.LabelFrame(frm, text=self._t("怪物图鉴"))
        f_monster.pack(padx=10, pady=5, fill="x")
        ttk.Button(f_monster, text=self._t("一键全开怪物图鉴"), command=self._unlock_all_monsters).pack(side="left", padx=5, pady=5)

    # ---- 数据绑定 ----
    def _refresh_all(self):
        s = self.save
        # 基本
        self._var("mira").set(str(s.read_u32(OFFSETS["mira"])))
        self._var("dp").set(str(s.read_u32(OFFSETS["dp"])))
        self._var("medal").set(str(s.read_u32(OFFSETS["medal"])))
        for name, off in SEPITH_OFFSETS.items():
            self._var(f"sepith_{name}").set(str(s.read_u32(off)))
        ts = s.read_u32(OFFSETS["time_s"])
        self._var("time_s").set(str(ts))
        self._var("time_h").set(str(ts // 3600))
        self._var("time_m").set(str((ts % 3600) // 60))
        self._var("time_sec").set(str(ts % 60))
        self._var("difficulty").set(str(s.read_u8(OFFSETS["difficulty"])))

        # 角色
        for name, base in CHAR_BASES.items():
            for attr, rel in CHAR_ATTR.items():
                off = base + rel
                if attr in ("max_hp","hp","exp"):
                    val = s.read_u32(off)
                else:
                    val = s.read_u16(off)
                self._var(f"char_{name}_{attr}").set(str(val))

        # 队伍
        for i, off in enumerate(TEAM_SLOTS):
            self._var(f"team_{i}").set(str(s.read_u16(off)))

        # 好感度
        for name, off in LIKEABILITY.items():
            self._var(f"like_{name}").set(str(s.read_u8(off)))

        # 物品
        self._items_data = s.read_items()

        # P0: 成就 + 战斗
        self._refresh_achievements_ui()
        self._refresh_battle_ui()
        # P1: 外观
        self._refresh_appearance_ui()

        # 刷新物品列表 UI
        self._refresh_items_ui()

    def _on_char_edit(self, offset, valtype, event):
        """角色属性编辑时写回"""
        if self.save.data is None:
            return
        widget = event.widget
        varname = widget.cget("textvariable")
        if isinstance(varname, str):
            sv = self._var(varname if varname else "")
            try:
                val = int(sv.get())
            except ValueError:
                return
        else:
            try:
                val = int(widget.get())
            except ValueError:
                return
        if valtype == "u32":
            self.save.write_u32(offset, val)
        else:
            self.save.write_u16(offset, val)

    def _write_all_from_gui(self):
        """从 GUI 所有输入框写入存档"""
        s = self.save
        if s.data is None:
            return
        try:
            s.write_u32(OFFSETS["mira"], int(self._var("mira").get()))
            s.write_u32(OFFSETS["dp"], int(self._var("dp").get()))
            s.write_u32(OFFSETS["medal"], int(self._var("medal").get()))
            for name, off in SEPITH_OFFSETS.items():
                s.write_u32(off, int(self._var(f"sepith_{name}").get()))
            h = int(self._var("time_h").get())
            m = int(self._var("time_m").get())
            sec = int(self._var("time_sec").get())
            s.write_u32(OFFSETS["time_s"], h * 3600 + m * 60 + sec)
            s.write_u8(OFFSETS["difficulty"], int(self._var("difficulty").get()))
        except ValueError:
            pass

        for name, base in CHAR_BASES.items():
            for attr, rel in CHAR_ATTR.items():
                off = base + rel
                try:
                    val = int(self._var(f"char_{name}_{attr}").get())
                except ValueError:
                    continue
                if attr in ("max_hp","hp","exp"):
                    s.write_u32(off, val)
                else:
                    s.write_u16(off, val)

        for i, off in enumerate(TEAM_SLOTS):
            try:
                s.write_u16(off, int(self._var(f"team_{i}").get()))
            except ValueError:
                pass

        for name, off in LIKEABILITY.items():
            try:
                s.write_u8(off, int(self._var(f"like_{name}").get()))
            except ValueError:
                pass

        # 物品
        s.write_items(self._items_data)

        # P0: 成就 + 战斗
        self._write_achievements_from_gui()
        self._write_battle_from_gui()
        # P1: 外观
        self._write_appearance_from_gui()

    def _quick_set(self, varname, val):
        self._var(varname).set(str(val))
        self._write_all_from_gui()
        self._set_status("已设置 {varname} = {val}", varname=varname, val=val)

    def _quick_max_sepith(self):
        for name in SEPITH_OFFSETS:
            self._var(f"sepith_{name}").set("9999")
        self._write_all_from_gui()
        self._set_status("全耀晶片 → 9999")

    def _quick_max_char(self, name):
        try:
            base = CHAR_BASES[name]
        except KeyError:
            return
        s = self.save
        if s.data is None:
            return
        lv = max(s.read_u16(base + CHAR_ATTR["lv"]), 1)
        hp = 99999
        s.write_u16(base + CHAR_ATTR["lv"], 99)
        s.write_u32(base + CHAR_ATTR["max_hp"], hp)
        s.write_u32(base + CHAR_ATTR["hp"], hp)
        s.write_u16(base + CHAR_ATTR["max_ep"], 999)
        s.write_u16(base + CHAR_ATTR["ep"], 999)
        s.write_u16(base + CHAR_ATTR["cp"], 200)
        s.write_u16(base + CHAR_ATTR["str"], 9999)
        s.write_u16(base + CHAR_ATTR["def"], 9999)
        s.write_u16(base + CHAR_ATTR["ats"], 9999)
        s.write_u16(base + CHAR_ATTR["adf"], 9999)
        self._refresh_all()
        self._set_status("{name} 已满属性", name=name)

    def _quick_max_like(self):
        s = self.save
        if s.data is None:
            return
        for off in LIKEABILITY.values():
            s.write_u8(off, 255)
        self._refresh_all()
        self._set_status("全员好感度 → 255")

    # ---- 物品快捷 ----
    def _quick_max_consumables(self):
        """消耗品、食材、书籍等设 99，并补齐缺失条目。"""
        if self.save.data is None:
            return
        self._items_data = self.save.read_items()
        for code in item_codes_for_categories("props_normal", "props_cooking", "food", "book", "fishing_bait", "fishing_fish"):
            self._items_data[code] = 99
        self.save.write_items(self._items_data)
        self._refresh_items_ui()
        self._set_status("全消耗品/食材/书籍/鱼 → 99")

    def _quick_max_circuits(self):
        """全回路(普通+核心)设 99，并补齐缺失条目。"""
        if self.save.data is None:
            return
        self._items_data = self.save.read_items()
        for code in item_codes_for_categories("circuit_normal", "circuit_core"):
            self._items_data[code] = 99
        self.save.write_items(self._items_data)
        self._refresh_items_ui()
        self._set_status("全回路 → 99")

    def _quick_max_equipment(self):
        """全装备(武器/服装/鞋子/饰品)设 1，并补齐缺失条目。"""
        if self.save.data is None:
            return
        self._items_data = self.save.read_items()
        for code in item_codes_by_prefix("equipment", "fishing_rod"):
            self._items_data[code] = 1
        self.save.write_items(self._items_data)
        self._refresh_items_ui()
        self._set_status("全装备 → 1")

    # ---- P0: 成就标签页 ----
    def _build_achievement_tab(self, frm):
        self._ach_vars = []  # list of (part, bit, BooleanVar, checkbox)
        canvas = tk.Canvas(frm)
        scrollbar = ttk.Scrollbar(frm, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        bar = ttk.Frame(scrollable)
        bar.pack(fill="x", padx=5, pady=5)
        ttk.Button(bar, text="全解锁", command=self._ach_unlock_all).pack(side="left", padx=3)
        ttk.Button(bar, text="全锁定", command=self._ach_lock_all).pack(side="left", padx=3)
        for part, bit, name in ACHIEVEMENT_NAMES:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(scrollable, text=achievement_name(part, bit, name, self._current_achievement_language()), variable=var)
            cb.pack(anchor="w", padx=15, pady=1)
            self._ach_vars.append((part, bit, var, cb))

    def _current_achievement_language(self):
        return self._current_ui_language()

    def _on_achievement_language_changed(self, _event=None):
        lang = self._current_achievement_language()
        name_by_key = {(part, bit): name for part, bit, name in ACHIEVEMENT_NAMES}
        for part, bit, _var, checkbox in self._ach_vars:
            zh_name = name_by_key.get((part, bit), "")
            checkbox.configure(text=achievement_name(part, bit, zh_name, lang))

    def _refresh_achievements_ui(self):
        if self.save.data is None:
            return
        bits = self.save.read_achievements()
        for part, bit, var, checkbox in self._ach_vars:
            var.set(bool(bits.get(part, [0]*8)[bit]))
        self._on_achievement_language_changed()

    def _write_achievements_from_gui(self):
        bits = {i: [0]*8 for i in range(7)}
        for part, bit, var, _checkbox in self._ach_vars:
            if var.get():
                bits[part][bit] = 1
        self.save.write_achievements(bits)

    def _ach_unlock_all(self):
        self._write_achievements_from_gui()
        bits = {i: [1]*8 for i in range(7)}
        self.save.write_achievements(bits)
        self._refresh_achievements_ui()
        self._set_status("全成就已解锁")

    def _ach_lock_all(self):
        bits = {i: [0]*8 for i in range(7)}
        self.save.write_achievements(bits)
        self._refresh_achievements_ui()
        self._set_status("全成就已锁定")

    # ---- P0: 战斗手册标签页 ----
    def _build_battle_tab(self, frm):
        frm.grid_columnconfigure(0, weight=1)
        ttk.Label(frm, text=self._t("战斗统计数据 (修改后保存生效)"), font=("", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        self._battle_vars = {}
        for i, (name, off) in enumerate(BATTLE_STATS.items()):
            ttk.Label(frm, text=self._t(name)).grid(row=i+1, column=0, sticky="e", padx=5, pady=2)
            var = tk.StringVar(value="0")
            ttk.Entry(frm, textvariable=var, width=12).grid(row=i+1, column=1, sticky="w", padx=5)
            self._battle_vars[name] = var

    def _refresh_battle_ui(self):
        if self.save.data is None:
            return
        for name, off in BATTLE_STATS.items():
            self._battle_vars[name].set(str(self.save.read_u16(off)))

    def _write_battle_from_gui(self):
        if self.save.data is None:
            return
        for name, off in BATTLE_STATS.items():
            try:
                self.save.write_u16(off, int(self._battle_vars[name].get()))
            except ValueError:
                pass

    # ---- P1: 角色外观标签页 ----
    def _build_appearance_tab(self, frm):
        frm.grid_columnconfigure(0, weight=1)
        ttk.Label(frm, text=self._t("角色显示外观 (修改对应槽位的模型)"), font=("", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        SLOT_LABELS = ["显示1","显示2","显示3","显示4","显示5","显示6",
                       "显示7","显示8","显示9","显示10","显示11","显示12"]
        self._appearance_vars = []
        self._appearance_combos = []
        opts = [f"{k}:{role_display_name(k, self._current_ui_language())}" for k in sorted(ROLE_DISPLAY_NAMES)]

        for i in range(12):
            ttk.Label(frm, text=self._t(SLOT_LABELS[i])).grid(row=i+1, column=0, sticky="e", padx=5, pady=2)
            var = tk.StringVar(value=f"0:{role_display_name(0, self._current_ui_language())}")
            cb = ttk.Combobox(frm, textvariable=var, values=opts, width=20, state="readonly")
            cb.grid(row=i+1, column=1, sticky="w", padx=5)
            self._appearance_vars.append((ROLE_DISPLAY_OFFSETS[i], var))
            self._appearance_combos.append(cb)

    def _refresh_appearance_ui(self):
        if self.save.data is None:
            return
        lang = self._current_ui_language()
        for off, var in self._appearance_vars:
            val = self.save.read_u16(off)
            name = role_display_name(val, lang)
            var.set(f"{val}:{name}")
        if hasattr(self, "_appearance_combos"):
            opts = [f"{k}:{role_display_name(k, lang)}" for k in sorted(ROLE_DISPLAY_NAMES)]
            for cb in self._appearance_combos:
                cb.configure(values=opts)

    def _write_appearance_from_gui(self):
        if self.save.data is None:
            return
        for off, var in self._appearance_vars:
            try:
                val = int(var.get().split(":")[0])
                self.save.write_u16(off, val)
            except (ValueError, IndexError):
                pass

    # ---- P1: 怪物图鉴一键全开 ----
    def _unlock_all_monsters(self):
        if self.save.data is None:
            return
        self.save.unlock_all_monsters()
        self._set_status("怪物图鉴已全开 · 请保存存档")

    # ---- 快捷操作 ----

    def _open_file(self):
        fp = filedialog.askopenfilename(
            title=self._t("选择 savedata.dat"),
            filetypes=[("savedata.dat", "*.dat"), ("所有文件", "*.*")]
        )
        if not fp:
            return
        try:
            loaded = self.save.load(fp)
        except RuntimeError as exc:
            messagebox.showerror(self._t("错误"), str(exc))
            return
        if loaded:
            self._refresh_all()
            fname = os.path.basename(fp)
            fdir = os.path.basename(os.path.dirname(fp))
            self._set_status("已加载: ...{fdir}/{fname}  ({size} bytes)", fdir=fdir, fname=fname, size=len(self.save.data))
        else:
            messagebox.showerror(self._t("错误"), self._t("无法解析存档:\n{fp}\n\n文件可能是加密的或格式不正确。", fp=fp))

    def _save_file(self):
        if self.save.data is None:
            messagebox.showwarning(self._t("提示"), self._t("请先打开存档文件"))
            return
        self._write_all_from_gui()
        fp = filedialog.asksaveasfilename(
            title=self._t("保存为"),
            defaultextension=".dat",
            filetypes=[("savedata.dat", "*.dat")],
            initialfile="savedata.dat"
        )
        if not fp:
            return
        try:
            self.save.save(fp)
        except (RuntimeError, ValueError, OSError) as exc:
            messagebox.showerror(self._t("错误"), str(exc))
            return
        self._set_status("已保存到: {fp}", fp=fp)
        messagebox.showinfo(self._t("完成"), self._t("存档已保存到:\n{fp}\n\n备份已自动创建为 .bak\n请将文件放回游戏存档目录替换原文件。", fp=fp))


def cli_quick_edit(filepath, mira=None, sepith=None, dp=None, max_chars=None, max_like=False):
    """命令行快速修改 (非GUI模式)"""
    s = SaveData()
    try:
        loaded = s.load(filepath)
    except RuntimeError as exc:
        print(f"错误: {exc}")
        return False
    if not loaded:
        print(f"错误: 无法加载 {filepath}")
        return False
    changed = False

    if mira is not None:
        s.write_u32(OFFSETS["mira"], int(mira))
        print(f"Mira -> {mira}")
        changed = True
    if dp is not None:
        s.write_u32(OFFSETS["dp"], int(dp))
        print(f"DP -> {dp}")
        changed = True
    if sepith == "max":
        for off in SEPITH_OFFSETS.values():
            s.write_u32(off, 9999)
        print("全耀晶片 -> 9999")
        changed = True
    if max_chars:
        for name in (max_chars.split(",") if max_chars != "all" else CHAR_BASES.keys()):
            name = name.strip()
            if name in CHAR_BASES:
                base = CHAR_BASES[name]
                s.write_u16(base + CHAR_ATTR["lv"], 99)
                s.write_u32(base + CHAR_ATTR["max_hp"], 99999)
                s.write_u32(base + CHAR_ATTR["hp"], 99999)
                s.write_u16(base + CHAR_ATTR["max_ep"], 999)
                s.write_u16(base + CHAR_ATTR["ep"], 999)
                s.write_u16(base + CHAR_ATTR["cp"], 200)
                s.write_u16(base + CHAR_ATTR["str"], 9999)
                s.write_u16(base + CHAR_ATTR["def"], 9999)
                s.write_u16(base + CHAR_ATTR["ats"], 9999)
                s.write_u16(base + CHAR_ATTR["adf"], 9999)
                print(f"{name} -> LV99 MAX")
                changed = True
    if max_like:
        for off in LIKEABILITY.values():
            s.write_u8(off, 255)
        print("全员好感度 -> 255")
        changed = True

    if changed:
        try:
            s.save(filepath)
        except RuntimeError as exc:
            print(f"错误: {exc}")
            return False
        print(f"已保存: {filepath}")
        return True
    else:
        print("未指定任何修改。用法: --mira 9999999 --sepith max --dp 400 --max-chars all --max-like")
        return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="碧之轨迹 NISA版 存档修改器")
    parser.add_argument("file", nargs="?", help="savedata.dat 路径 (GUI模式可省略)")
    parser.add_argument("--mira", help="设置 Mira")
    parser.add_argument("--dp", help="设置 DP")
    parser.add_argument("--sepith", choices=["max"], help="全耀晶片最大化")
    parser.add_argument("--max-chars", help="角色满属性 (all 或 逗号分隔的名字, 如: Lloyd,Elie)")
    parser.add_argument("--max-like", action="store_true", help="全员好感度满")
    args = parser.parse_args()

    has_cli = any([args.mira, args.dp, args.sepith, args.max_chars, args.max_like])
    if has_cli and args.file:
        cli_quick_edit(args.file, args.mira, args.sepith, args.dp, args.max_chars, args.max_like)
    else:
        app = SaveEditor()
        app.mainloop()
