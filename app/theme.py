# -*- coding: utf-8 -*-
"""主题引擎：亮 / 暗 / 灰 三套色板 + 自定义主题色（强调色），支持磨砂透明模式。

build_qss(frosted, theme, accent) 生成全局 QSS：
- theme：dark（深空蓝）/ light（亮白）/ gray（中性灰）
- accent：主题色（按钮渐变、选中高亮、强调文字），可 RGB 自定义
- frosted：磨砂透明（面板容器自绘半透明底，控件透明，透出背景层）
"""

from PySide6.QtGui import QColor

# ---------------------------------------------------------------------------
# 三套色板
# ---------------------------------------------------------------------------
PALETTES = {
    "dark": {
        "label": "暗",
        "bg": "#0B0F14",        # 窗口背景
        "panel": "#0D1420",     # 面板（状态栏/树/标签面板）
        "panel2": "#0F1622",    # 分组框
        "input": "#0B1119",     # 输入控件
        "focus_bg": "#0C1420",  # 输入聚焦背景
        "text": "#E5EBF3",      # 主文字
        "text2": "#8A94A6",     # 次要文字
        "text3": "#C7D2E0",     # 常规文字
        "border": "#1E2A3A",
        "border2": "#24303F",
        "hover": "#16202E",
        "menu": "#121B2A",
        "tab": "#101826",
        "bar": "#1C1712",       # 栏/面板/对话框基础色调（浅棕黑）
    },
    "light": {
        "label": "亮",
        "bg": "#F3F4F6",
        "panel": "#FFFFFF",
        "panel2": "#EDEFF2",
        "input": "#FFFFFF",
        "focus_bg": "#FFFFFF",
        "text": "#1F2328",
        "text2": "#6E7781",
        "text3": "#24292F",
        "border": "#D0D7DE",
        "border2": "#D8DEE4",
        "hover": "#E8EBEF",
        "menu": "#FFFFFF",
        "tab": "#F0F2F5",
        "bar": "#F8F7F5",       # 栏/面板/对话框基础色调（浅亮白）
    },
    "gray": {
        "label": "灰",
        "bg": "#23272E",
        "panel": "#2A2F36",
        "panel2": "#2F353D",
        "input": "#262B32",
        "focus_bg": "#262B32",
        "text": "#E6EDF3",
        "text2": "#9BA6B2",
        "text3": "#D0D7DE",
        "border": "#3A4149",
        "border2": "#454D56",
        "hover": "#333A42",
        "menu": "#2A2F36",
        "tab": "#282D34",
        "bar": "#26201A",       # 栏/面板/对话框基础色调（浅棕黑，略亮）
    },
}

DEFAULT_ACCENT = "#1E5EFF"

# 主题色快捷选择（偏浅色系）
QUICK_ACCENTS = [
    ("浅蓝", "#5B9DFF"), ("浅紫", "#A78BFA"), ("浅粉", "#F472B6"),
    ("浅青", "#34D6C4"), ("浅橙", "#FFB84D"), ("浅绿", "#6FCF7E"),
    ("浅红", "#FF7B7B"), ("浅黄", "#F6D365"),
]


def _rgba(hex_color, alpha):
    c = QColor(hex_color)
    return f"rgba({c.red()}, {c.green()}, {c.blue()}, {alpha})"


def panel_bar(theme="dark"):
    """栏/面板基础色调 RGB 元组（dark/gray = 浅棕黑，light = 浅亮白）。

    供 FrostedPanel 等自绘容器使用；alpha 由透明度逻辑单独控制。
    """
    p = PALETTES.get(theme, PALETTES["dark"])
    c = QColor(p["bar"])
    return (c.red(), c.green(), c.blue())


# ---------------------------------------------------------------------------
# QSS 模板（占位符版）
# ---------------------------------------------------------------------------
_QSS = """
* { outline: none; }
QMainWindow {
    background-color: __BG_MAIN__;
    color: __TEXT__;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QWidget {
    background-color: __BG_WIDGET__;
    color: __TEXT__;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ---- 状态栏（左下角门类切换） ---- */
QStatusBar {
    background-color: __BAR_SB__;
    border-top: 1px solid __BORDER__;
    color: __TEXT2__;
}
QStatusBar QToolButton {
    background: transparent;
    color: __TEXT3__;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 3px 10px;
    margin: 2px;
    font-size: 12px;
}
QStatusBar QToolButton:hover {
    background: __HOVER__;
    color: __TEXT__;
    border-color: __BORDER2__;
}
QStatusBar QToolButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 __ACCENT__, stop:1 __ACCENT2__);
    color: #FFFFFF;
    font-weight: 600;
    border: none;
}

/* ---- 分割条 ---- */
QSplitter::handle { background: transparent; }
QSplitter::handle:hover { background: __ACCENT__; }

/* ---- 项目树 ---- */
QTreeWidget {
    background-color: __PANEL__;
    border: none;
    padding: 4px;
}
QTreeWidget::item {
    color: __TEXT3__;
    padding: 5px 4px;
    border-radius: 5px;
    margin: 1px 0;
}
QTreeWidget::item:hover { background: __HOVER__; }
QTreeWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 __SEL1__, stop:1 __SEL2__);
    color: #FFFFFF;
}
QTreeWidget::branch { background: transparent; }

/* ---- 标签页 ---- */
QTabWidget::pane {
    border: 1px solid __BORDER__;
    border-radius: 8px;
    background: __PANEL__;
    top: -1px;
}
QTabBar::tab {
    background: __TAB__;
    color: __TEXT2__;
    padding: 7px 16px;
    margin-right: 2px;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:hover { background: __HOVER__; color: __TEXT__; }
QTabBar::tab:selected {
    background: __TAB_SEL__;
    color: __TEXT__;
    border-color: __BORDER__ __BORDER__ __TAB_SEL__ __BORDER__;
    border-bottom: 2px solid __ACCENT__;
}

/* ---- 输入控件 ---- */
QPlainTextEdit, QTextEdit, QLineEdit {
    background-color: __INPUT__;
    color: __TEXT__;
    border: 1px solid __BORDER2__;
    border-radius: 6px;
    padding: 4px;
    selection-background-color: __ACCENT__;
    selection-color: #FFFFFF;
}
QPlainTextEdit:focus, QTextEdit:focus, QLineEdit:focus {
    border: 1px solid __ACCENT__;
    background-color: __FOCUS_BG__;
}
QLineEdit { padding: 5px 8px; }

/* ---- 按钮 ---- */
QPushButton {
    background-color: __HOVER__;
    color: __TEXT__;
    border: 1px solid __BORDER2__;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover { background-color: __PANEL2__; border-color: __ACCENT__; }
QPushButton:pressed { background-color: __INPUT__; }
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 __ACCENT__, stop:1 __ACCENT2__);
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 __ACCENT_H__, stop:1 __ACCENT2_H__);
}

QToolButton {
    background: transparent;
    color: __TEXT3__;
    border-radius: 5px;
    padding: 4px 8px;
}
QToolButton:hover { background: __HOVER__; color: __TEXT__; }
QToolButton#del_btn { color: #E57B7B; }
QToolButton#del_btn:hover { background: #3D1520; color: #FF8A8A; }

/* ---- 表格（chat 模式） ---- */
QTableWidget {
    background-color: __INPUT__;
    alternate-background-color: __PANEL2__;
    color: __TEXT__;
    border: 1px solid __BORDER2__;
    border-radius: 6px;
    gridline-color: __BORDER__;
}
QTableWidget::item { padding: 4px; }
QHeaderView::section {
    background-color: __PANEL2__;
    color: __TEXT2__;
    border: none;
    border-bottom: 1px solid __BORDER2__;
    padding: 6px;
    font-weight: 600;
}
QTableCornerButton::section { background: __PANEL2__; border: none; }

/* ---- 下拉框 ---- */
QComboBox {
    background-color: __INPUT__;
    color: __TEXT__;
    border: 1px solid __BORDER2__;
    border-radius: 6px;
    padding: 5px 10px;
}
QComboBox:hover { border-color: __ACCENT__; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow {
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid __TEXT2__;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: __MENU__;
    color: __TEXT__;
    border: 1px solid __BORDER2__;
    selection-background-color: __ACCENT__;
    selection-color: #FFFFFF;
    outline: none;
}

/* ---- 分组框 / 列表 ---- */
QGroupBox {
    background-color: __PANEL2__;
    border: 1px solid __BORDER__;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: 600;
    color: __TEXT3__;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: __TITLE__;
}
QListWidget {
    background-color: __INPUT__;
    color: __TEXT__;
    border: 1px solid __BORDER2__;
    border-radius: 6px;
}
QListWidget::item { padding: 6px; border-radius: 5px; }
QListWidget::item:hover { background: __HOVER__; }
QListWidget::item:selected { background: __ACCENT__; color: #FFFFFF; }

/* ---- 滚动条 ---- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: __BORDER2__; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: __ACCENT__; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: __BORDER2__; border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: __ACCENT__; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---- 右键菜单 ---- */
QMenu {
    background-color: __MENU__;
    color: __TEXT__;
    border: 1px solid __BORDER2__;
    border-radius: 8px;
    padding: 5px;
}
QMenu::item { padding: 7px 24px; border-radius: 5px; }
QMenu::item:selected { background: __ACCENT__; color: #FFFFFF; }
QMenu::separator { height: 1px; background: __BORDER__; margin: 5px 8px; }

/* ---- 对话框 / 文本 ---- */
QDialog { background-color: __BAR__; }
QMessageBox, QInputDialog { background-color: __BAR__; }
QLabel { color: __TEXT__; }
QDialogButtonBox QPushButton { min-width: 80px; }
QToolTip {
    background-color: __MENU__;
    color: __TEXT__;
    border: 1px solid __ACCENT__;
    border-radius: 5px;
    padding: 5px 8px;
}
"""


def _resolved_vals(theme, accent_hex, frosted):
    p = PALETTES.get(theme, PALETTES["dark"])
    ac = QColor(accent_hex)
    if not ac.isValid():
        ac = QColor(DEFAULT_ACCENT)
    accent = ac.name()
    accent2 = ac.lighter(125).name()
    accent_h = ac.lighter(112).name()
    accent2_h = ac.lighter(135).name()
    sel1 = ac.darker(115).name()
    sel2 = ac.darker(145).name()
    title = ac.lighter(108).name()

    vals = {
        "__BG_MAIN__": p["bg"],
        "__BG_WIDGET__": p["bg"] if not frosted else "transparent",
        "__PANEL__": p["panel"] if not frosted else "transparent",
        "__PANEL2__": p["panel2"] if not frosted else "transparent",
        # 磨砂模式下输入/菜单/标签等统一用「栏色调」（dark/gray 浅棕黑、light 浅亮白）+ alpha
        "__INPUT__": p["input"] if not frosted else _rgba(p["bar"], 150),
        "__FOCUS_BG__": p["focus_bg"] if not frosted else _rgba(p["bar"], 165),
        "__MENU__": p["menu"] if not frosted else _rgba(p["bar"], 230),
        "__TAB__": p["tab"] if not frosted else _rgba(p["bar"], 140),
        "__TAB_SEL__": p["panel"] if not frosted else _rgba(p["bar"], 170),
        # 对话框 / 状态栏底色（磨砂时半透明，避免顶层窗口透明显示成纯黑）
        "__BAR__": p["bar"] if not frosted else _rgba(p["bar"], 245),
        "__BAR_SB__": p["bar"] if not frosted else _rgba(p["bar"], 210),
        "__TEXT__": p["text"],
        "__TEXT2__": p["text2"],
        "__TEXT3__": p["text3"],
        "__BORDER__": p["border"],
        "__BORDER2__": p["border2"],
        "__HOVER__": p["hover"],
        "__ACCENT__": accent,
        "__ACCENT2__": accent2,
        "__ACCENT_H__": accent_h,
        "__ACCENT2_H__": accent2_h,
        "__SEL1__": sel1,
        "__SEL2__": sel2,
        "__TITLE__": title,
    }
    return vals


def build_qss(frosted=False, theme="dark", accent=DEFAULT_ACCENT):
    """生成全局 QSS。theme 见 PALETTES；accent 为主题色（按钮/选中/强调文字）。"""
    qss = _QSS
    for token, val in _resolved_vals(theme, accent, frosted).items():
        qss = qss.replace(token, val)
    if frosted:
        # 面板容器自绘半透明底（FrostedPanel），QSS 保持透明
        # （输入/菜单/标签等底色已由 __INPUT__/__MENU__/__TAB__ 用栏色调+alpha 主题化）
        qss += (
            "\n/* ---- 磨砂模式：面板容器透明（底色由 FrostedPanel 自绘） ---- */\n"
            "#SidePanel, #EditorArea, #RightPanel {\n"
            "    background-color: transparent;\n"
            "}\n"
        )
    return qss


# 兼容旧引用
TECH_STYLE = build_qss(False, "dark")
