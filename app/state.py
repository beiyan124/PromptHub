# -*- coding: utf-8 -*-
"""设置与状态持久化。

- config.json（数据目录下）：整体用户设置（背景 + 主题），
  启动时读取、无则新建默认；修改后需点「保存设置」才写盘。
- .state.json（数据目录下）：UI 状态（左侧树展开状态树），即时持久化，不属于 config。
"""

import json
import os

from . import config


# ---------------------------------------------------------------------------
# 整体设置（config.json）
# ---------------------------------------------------------------------------
def config_path():
    """整体设置文件路径（跟随 DATA_DIR）。"""
    return os.path.join(config.DATA_DIR, "config.json")


_cfg = None  # 内存缓存（设置修改先更新内存，保存时写盘）


def _default_config():
    return {
        "background": {
            "enabled": True,     # 默认开启磨砂透明
            "image": "",
            "blur": 24,          # 模糊滑块 0-50
            "dim": 0,            # 遮罩滑块 0-100（默认 0 = 无遮罩，亮度为图片本身）
            "panel_opacity": 65, # 左中右面板透明度 0-100（0=几乎全透明，100=不透明）
        },
        "theme": {
            "name": "dark",
            "accent": "#1E5EFF",
        },
    }


def load_config():
    """读取整体设置；config.json 不存在或损坏时新建默认文件。
    兼容迁移：若旧 .state.json 中有 background/theme，作为首次默认。"""
    global _cfg
    if _cfg is not None:
        return _cfg
    if os.path.exists(config_path()):
        try:
            with open(config_path(), encoding="utf-8") as f:
                _cfg = json.load(f)
            return _cfg
        except Exception:
            pass
    # 从旧 .state.json 迁移外观设置
    old = {}
    try:
        with open(state_path(), encoding="utf-8") as f:
            old = json.load(f)
    except Exception:
        pass
    _cfg = _default_config()
    if old.get("background"):
        _cfg["background"].update(old["background"])
    if old.get("theme"):
        _cfg["theme"].update(old["theme"])
    save_config()
    return _cfg


def save_config(cfg=None):
    """保存整体设置到 config.json（「保存设置」按钮 / 关窗时调用）。"""
    global _cfg
    if cfg is not None:
        _cfg = cfg
    if _cfg is None:
        _cfg = _default_config()
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(config_path(), "w", encoding="utf-8") as f:
            json.dump(_cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def has_unsaved():
    """是否有未保存的设置修改（config 文件内容与内存不一致）。"""
    if _cfg is None:
        return False
    try:
        with open(config_path(), encoding="utf-8") as f:
            return json.load(f) != _cfg
    except Exception:
        return True


# ---- 背景 ----
def get_background():
    c = load_config().get("background", {})
    return {
        "enabled": bool(c.get("enabled", True)),
        "image": c.get("image", ""),
        "blur": max(0, min(50, int(c.get("blur", 24)))),
        "dim": max(0, min(100, int(c.get("dim", 0)))),
        "panel_opacity": max(0, min(100, int(c.get("panel_opacity", 65)))),
    }


def set_background(bg):
    """更新背景设置（仅内存，调用 save_config 持久化）。"""
    c = load_config()
    c["background"] = {
        "enabled": bool(bg.get("enabled", True)),
        "image": bg.get("image", ""),
        "blur": max(0, min(50, int(bg.get("blur", 24)))),
        "dim": max(0, min(100, int(bg.get("dim", 0)))),
        "panel_opacity": max(0, min(100, int(bg.get("panel_opacity", 65)))),
    }


# ---- 主题 ----
def get_theme():
    t = load_config().get("theme", {})
    return {
        "name": t.get("name", "dark"),
        "accent": t.get("accent", "#1E5EFF"),
    }


def set_theme(name, accent):
    """更新主题设置（仅内存，调用 save_config 持久化）。"""
    c = load_config()
    c["theme"] = {"name": name, "accent": accent}


# ---------------------------------------------------------------------------
# UI 状态（.state.json，即时持久化）
# ---------------------------------------------------------------------------
def state_path():
    """UI 状态文件路径（跟随 DATA_DIR）。"""
    return os.path.join(config.DATA_DIR, ".state.json")


def _load_state():
    try:
        with open(state_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(st):
    try:
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(state_path(), "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---- 左侧树展开状态树 ----
def get_expanded():
    """返回展开状态树：{门类: {项目: bool}}。"""
    return _load_state().get("expanded", {})


def set_expanded(expanded_map):
    """写入展开状态树（即时持久化）。"""
    st = _load_state()
    st["expanded"] = expanded_map
    _save_state(st)
