#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词管理器 — 入口
====================
VSCode 式布局 · JSON 存储 · 支持纯文本 / 多轮消息 / 嵌套结构三种内容模式 · 提示词片间关联

层级：四大门类（文本/绘图/视频/音频） → 项目（文件夹） → 提示词片（.json 文件）
运行：python main.py  （或双击 run.bat）
"""

import os
import sys

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app import config, state
from app.theme import build_qss
from app.ui.main_window import MainWindow


def _install_zh_translator(app):
    """加载 Qt 自带中文翻译（汉化标准按钮：保存/放弃/取消/是/否/确定 等）。

    PySide6 安装包自带 translations/qtbase_zh_CN.qm，通过 QLibraryInfo 定位。
    """
    try:
        translator = QTranslator(app)
        path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        if translator.load("qtbase_zh_CN", path):
            app.installTranslator(translator)
    except Exception:
        pass  # 找不到翻译文件时保持原样（按钮显示英文），不影响主流程


def _set_window_icon(app):
    """设置窗口 / 任务栏图标（多尺寸 logo/app.ico）。

    打包后图标随包解压到 _MEIPASS/logo/app.ico；开发时读取项目 logo/ 目录。
    """
    try:
        base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        for cand in (os.path.join(base, "logo", "app.ico"),
                     os.path.join(base, "app.ico")):
            if os.path.isfile(cand):
                app.setWindowIcon(QIcon(cand))
                return
    except Exception:
        pass  # 找不到图标不影响主流程


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    _install_zh_translator(app)
    _set_window_icon(app)
    bg = state.get_background()
    t = state.get_theme()
    app.setStyleSheet(build_qss(
        bool(bg.get("enabled", False)),
        t.get("name", "dark"),
        t.get("accent", "#1E5EFF")))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
