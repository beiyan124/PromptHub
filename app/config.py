# -*- coding: utf-8 -*-
"""全局配置：应用信息、门类、路径（数据目录支持运行时修改）。"""

import os
import sys

# ---- 应用信息 ----
APP_NAME = "提示词管理器"
APP_VERSION = "1.12.3"
APP_CONTRIBUTORS = ["beiyan124", "workbuddy"]

# ---- 路径 ----
# 是否 PyInstaller 打包运行；程序所在目录 = exe 目录（开发时 = 项目根目录）
_FROZEN = getattr(sys, "frozen", False)
if _FROZEN:
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = APP_DIR

# 用户级配置目录（独立于数据目录；记录「当前数据目录位置」，不随数据迁移）
APP_DATA = os.path.join(
    os.environ.get("APPDATA") or os.path.expanduser("~"),
    APP_NAME,
)

# 默认数据目录名：程序（exe / 项目）同目录下的 PromtFile/
DEFAULT_DATA_NAME = "PromtFile"


def _default_data_dir():
    """默认数据目录：exe / 项目同目录下的 PromtFile 文件夹。"""
    return os.path.join(APP_DIR, DEFAULT_DATA_NAME)


def load_data_dir():
    """启动时读取记录的数据目录；无记录或记录失效时回退默认。

    数据目录路径必须持久化在独立位置（不能存在数据目录里，否则迁移后
    找不到 config.json → 重启又回默认目录）。
    """
    try:
        p = os.path.join(APP_DATA, "data_dir.txt")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                d = f.read().strip()
            if d and os.path.isdir(d):
                return d
    except Exception:
        pass
    return _default_data_dir()


def save_data_dir(path):
    """持久化当前数据目录到独立配置文件（迁移成功后调用）。"""
    try:
        os.makedirs(APP_DATA, exist_ok=True)
        with open(os.path.join(APP_DATA, "data_dir.txt"), "w", encoding="utf-8") as f:
            f.write(path)
    except Exception:
        pass


# 数据根目录（启动时从独立配置恢复；可通过设置界面修改，修改后所有数据自动搬运）
DATA_DIR = load_data_dir()

# ---- 固定四大门类 ----
CATEGORIES = ["文本", "绘图", "视频", "音频"]

# ---- 内容格式 ----
FORMATS = [("plain", "纯文本"), ("chat", "多轮消息"), ("tree", "嵌套结构")]
CHAT_ROLES = ["system", "user", "assistant"]
# 角色显示名（界面中文显示，JSON 中仍存英文值，兼容旧数据）
CHAT_ROLE_LABELS = {"system": "系统", "user": "用户", "assistant": "助手"}


def trash_dir():
    """回收站目录（随 DATA_DIR 变化）。"""
    return os.path.join(DATA_DIR, ".回收站")
