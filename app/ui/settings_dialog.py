# -*- coding: utf-8 -*-
"""设置对话框（IDE 风格）：左侧分类栏 + 右侧详情页。

顺序：关于 / 存储 / 外观（主题 + 磨砂背景）/ 快捷键
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QFileDialog, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QSlider, QStackedWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView,
)

from .. import config
from .. import models
from .. import state
from .. import theme

PAGE_ABOUT, PAGE_STORAGE, PAGE_APPEARANCE, PAGE_SHORTCUTS = 0, 1, 2, 3
PAGES = [("关于", PAGE_ABOUT), ("存储", PAGE_STORAGE), ("外观", PAGE_APPEARANCE), ("快捷键", PAGE_SHORTCUTS)]

SHORTCUTS = [
    ("保存当前提示词片", "Ctrl+S"),
    ("保存全部标签", "Ctrl+Shift+S"),
    ("新建项目", "Ctrl+Shift+N"),
    ("新建提示词片", "Ctrl+N"),
    ("聚焦搜索", "Ctrl+F"),
    ("重命名选中项", "F2"),
    ("删除选中项", "Delete"),
    ("刷新目录", "F5"),
    ("重新渲染背景", "Ctrl+Shift+R"),
    ("下一个标签", "Ctrl+Tab"),
    ("上一个标签", "Ctrl+Shift+Tab"),
    ("关闭当前标签", "Ctrl+W"),
    ("打开设置", "Ctrl+,"),
    ("退出程序", "Ctrl+Q"),
]


class SettingsDialog(QDialog):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.setWindowTitle("设置")
        self.resize(780, 540)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        # ---- 左侧分类栏 ----
        self.nav = QListWidget()
        self.nav.setFixedWidth(140)
        self.nav.setStyleSheet("QListWidget::item { padding: 10px 12px; font-size: 13px; }")
        for name, _ in PAGES:
            self.nav.addItem(QListWidgetItem(name))
        self.nav.currentRowChanged.connect(self._switch_page)
        lay.addWidget(self.nav)

        # ---- 右侧详情页 + 底部操作 ----
        right_wrap = QWidget()
        rv = QVBoxLayout(right_wrap)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(8)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_about_page())
        self.stack.addWidget(self._build_storage_page())
        self.stack.addWidget(self._build_appearance_page())
        self.stack.addWidget(self._build_shortcuts_page())
        rv.addWidget(self.stack, 1)

        bottom = QHBoxLayout()
        b_save = QPushButton("保存设置")
        b_save.setObjectName("primary")
        b_save.clicked.connect(self._save)
        b_close = QPushButton("关闭")
        b_close.clicked.connect(self.accept)
        bottom.addStretch()
        bottom.addWidget(b_save)
        bottom.addWidget(b_close)
        rv.addLayout(bottom)
        lay.addWidget(right_wrap, 1)

        self.nav.setCurrentRow(PAGE_ABOUT)

    def _save(self):
        """保存整体设置到 config.json。"""
        state.save_config()
        QMessageBox.information(self, "保存设置", "设置已保存到 config.json")

    def accept(self):
        """关闭窗口前自动保存未保存的设置修改。"""
        if state.has_unsaved():
            state.save_config()
        super().accept()

    def closeEvent(self, ev):
        if state.has_unsaved():
            state.save_config()
        super().closeEvent(ev)

    def _switch_page(self, row):
        if 0 <= row < self.stack.count():
            self.stack.setCurrentIndex(row)

    # ================= 关于页 =================
    def _build_about_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(8)
        g = QGroupBox("软件信息")
        f = QVBoxLayout(g)
        title = QLabel(f"{config.APP_NAME}")
        title.setStyleSheet("font-size:18px; font-weight:600; color:#22D3EE;")
        f.addWidget(title)
        f.addWidget(QLabel(f"版本：v{config.APP_VERSION}"))
        f.addWidget(QLabel(f"贡献者：{' · '.join(config.APP_CONTRIBUTORS)}"))
        f.addWidget(QLabel("技术栈：Python + PySide6 · JSON 本地存储"))
        f.addWidget(QLabel(f"数据目录：{config.DATA_DIR}"))
        f.addWidget(QLabel(f"回收站：{config.trash_dir()}"))
        lay.addWidget(g)
        lay.addStretch()
        return page

    # ================= 存储页 =================
    def _build_storage_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(8)
        g = QGroupBox("数据存储")
        f = QVBoxLayout(g)
        f.addWidget(QLabel("存储地址（可手动输入新路径，不存在会自动创建）："))
        row = QHBoxLayout()
        self.dir_edit = QLineEdit(config.DATA_DIR)
        self.dir_edit.setPlaceholderText("选择或输入数据目录…")
        b_browse = QPushButton("浏览…")
        b_browse.clicked.connect(self._browse_dir)
        row.addWidget(self.dir_edit, 1)
        row.addWidget(b_browse)
        f.addLayout(row)
        tip = QLabel(f"回收站：{config.trash_dir()}")
        tip.setStyleSheet("color:#8A94A6; font-size:11px;")
        f.addWidget(tip)
        ops = QHBoxLayout()
        b_open = QPushButton("在资源管理器中打开")
        b_open.clicked.connect(lambda: self.main.open_in_explorer(config.DATA_DIR))
        b_apply = QPushButton("应用并迁移…")
        b_apply.setObjectName("primary")
        b_apply.clicked.connect(self._migrate)
        ops.addWidget(b_open)
        ops.addStretch()
        ops.addWidget(b_apply)
        f.addLayout(ops)
        lay.addWidget(g)
        lay.addStretch()
        return page

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择数据目录", config.DATA_DIR)
        if d:
            self.dir_edit.setText(d)

    def _migrate(self):
        new_dir = self.dir_edit.text().strip()
        if not new_dir:
            QMessageBox.warning(self, "提示", "请先输入存储地址")
            return
        if os.path.abspath(new_dir) == os.path.abspath(config.DATA_DIR):
            QMessageBox.information(self, "提示", "目标目录与当前目录相同，无需迁移")
            return
        r = QMessageBox.question(
            self, "确认迁移",
            f"将把全部提示词（含项目层级与关联）搬运到：\n{new_dir}\n\n"
            f"原目录：{config.DATA_DIR}\n\n确定继续吗？",
            QMessageBox.Yes | QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        ok, msg = models.migrate_data_dir(new_dir)
        if not ok:
            QMessageBox.warning(self, "迁移失败", msg)
            return
        self.dir_edit.setText(config.DATA_DIR)
        self.main.on_data_dir_changed()
        QMessageBox.information(self, "迁移成功", f"数据已迁移到：\n{config.DATA_DIR}")

    # ================= 外观页（主题 + 磨砂背景） =================
    def _build_appearance_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(8)

        # ---- 主题 ----
        g0 = QGroupBox("主题")
        f0 = QVBoxLayout(g0)
        row0 = QHBoxLayout()
        row0.addWidget(QLabel("主题模式："))
        self.theme_combo = QComboBox()
        for key in ("dark", "light", "gray"):
            self.theme_combo.addItem(theme.PALETTES[key]["label"] + f"（{key}）", key)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_change)
        row0.addWidget(self.theme_combo)
        row0.addStretch()
        f0.addLayout(row0)

        f0.addWidget(QLabel("主题色（按钮 / 选中高亮 / 强调文字）："))
        swatch_row = QHBoxLayout()
        self.accent_preview = QLabel()
        self.accent_preview.setFixedSize(30, 26)
        self.accent_preview.setStyleSheet("border-radius:5px; border:1px solid #888;")
        swatch_row.addWidget(self.accent_preview)
        self.accent_btns = []
        for name, color in theme.QUICK_ACCENTS:
            b = QPushButton()
            b.setFixedSize(30, 26)
            b.setToolTip(f"{name} {color}")
            b.setStyleSheet(f"background-color:{color}; border:none; border-radius:5px;")
            b.clicked.connect(lambda _=False, c=color: self._set_accent(c))
            self.accent_btns.append(b)
            swatch_row.addWidget(b)
        b_custom = QPushButton("自定义…")
        b_custom.clicked.connect(self._custom_accent)
        swatch_row.addWidget(b_custom)
        swatch_row.addStretch()
        f0.addLayout(swatch_row)
        lay.addWidget(g0)

        # ---- 磨砂背景 ----
        g = QGroupBox("磨砂透明背景")
        f = QVBoxLayout(g)

        self.frosted_cb = QCheckBox("启用磨砂透明背景（应用后生效）")
        self.frosted_cb.toggled.connect(self._on_appearance_change)
        f.addWidget(self.frosted_cb)

        f.addWidget(QLabel("背景图片："))
        img_row = QHBoxLayout()
        self.img_edit = QLineEdit()
        self.img_edit.setReadOnly(True)
        self.img_edit.setPlaceholderText("未选择（使用内置默认背景）")
        b_pick = QPushButton("选择图片…")
        b_pick.clicked.connect(self._pick_image)
        img_row.addWidget(self.img_edit, 1)
        img_row.addWidget(b_pick)
        f.addLayout(img_row)

        self.preview = QLabel("预览")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedHeight(90)
        _tname = state.get_theme()["name"]
        _p2 = theme.PALETTES.get(_tname, theme.PALETTES["dark"])["panel2"]
        _bd = theme.PALETTES.get(_tname, theme.PALETTES["dark"])["border2"]
        self.preview.setStyleSheet(
            f"background:{_p2}; border:1px solid {_bd}; border-radius:6px; color:#8A94A6;")
        f.addWidget(self.preview)

        blur_row = QHBoxLayout()
        blur_row.addWidget(QLabel("模糊强度"))
        self.blur_slider = QSlider(Qt.Horizontal)
        self.blur_slider.setRange(0, 50)
        self.blur_slider.valueChanged.connect(self._on_appearance_change)
        blur_row.addWidget(self.blur_slider, 1)
        self.blur_val = QLabel("24")
        self.blur_val.setFixedWidth(28)
        blur_row.addWidget(self.blur_val)
        f.addLayout(blur_row)

        dim_row = QHBoxLayout()
        dim_row.addWidget(QLabel("遮罩深度"))
        self.dim_slider = QSlider(Qt.Horizontal)
        self.dim_slider.setRange(0, 100)
        self.dim_slider.valueChanged.connect(self._on_appearance_change)
        dim_row.addWidget(self.dim_slider, 1)
        self.dim_val = QLabel("0")
        self.dim_val.setFixedWidth(28)
        dim_row.addWidget(self.dim_val)
        f.addLayout(dim_row)

        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("面板透明度"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.valueChanged.connect(self._on_appearance_change)
        op_row.addWidget(self.opacity_slider, 1)
        self.opacity_val = QLabel("65")
        self.opacity_val.setFixedWidth(28)
        op_row.addWidget(self.opacity_val)
        f.addLayout(op_row)

        ops2 = QHBoxLayout()
        b_reset = QPushButton("恢复默认背景")
        b_reset.clicked.connect(self._reset_background)
        b_rerender = QPushButton("重新渲染")
        b_rerender.clicked.connect(self._force_render)
        ops2.addWidget(b_reset)
        ops2.addWidget(b_rerender)
        ops2.addStretch()
        f.addLayout(ops2)

        tip = QLabel("提示：建议选择 1920×1080 及以上分辨率的图片；模糊强度为线性曲线（拉满≈线性高斯的 1/3，"
                     "1~5 档几乎无模糊）；遮罩 0-100，100 时亮度约为原来的一半；面板透明度 0-100，"
                     "0 时左中右面板几乎全透明、透出背景。若渲染异常，点击「重新渲染」即可恢复。")
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#8A94A6; font-size:11px;")
        f.addWidget(tip)
        lay.addWidget(g)
        lay.addStretch()

        self._load_theme_ui()
        self._load_background_ui()
        return page

    # ---------- 主题 ----------
    def _load_theme_ui(self):
        t = state.get_theme()
        self.theme_combo.blockSignals(True)
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == t["name"]:
                self.theme_combo.setCurrentIndex(i)
                break
        self.theme_combo.blockSignals(False)
        self._refresh_accent_preview(t["accent"])

    def _refresh_accent_preview(self, accent):
        self.accent_preview.setStyleSheet(
            f"background-color:{accent}; border-radius:5px; border:1px solid #888;")

    def _on_theme_change(self):
        name = self.theme_combo.currentData()
        accent = state.get_theme()["accent"]
        state.set_theme(name, accent)
        self.main.apply_appearance()

    def _set_accent(self, color):
        self._refresh_accent_preview(color)
        state.set_theme(self.theme_combo.currentData(), color)
        self.main.apply_appearance()

    def _custom_accent(self):
        color = QColorDialog.getColor(QColor(state.get_theme()["accent"]), self, "选择主题色")
        if color.isValid():
            self._set_accent(color.name())

    # ---------- 磨砂背景 ----------
    def _load_background_ui(self):
        bg = state.get_background()
        self.frosted_cb.blockSignals(True)
        self.blur_slider.blockSignals(True)
        self.dim_slider.blockSignals(True)
        self.opacity_slider.blockSignals(True)
        self.frosted_cb.setChecked(bool(bg.get("enabled")))
        self.img_edit.setText(bg.get("image", ""))
        self.blur_slider.setValue(int(bg.get("blur", 24)))
        self.dim_slider.setValue(int(bg.get("dim", 0)))
        self.opacity_slider.setValue(int(bg.get("panel_opacity", 65)))
        self.blur_val.setText(str(self.blur_slider.value()))
        self.dim_val.setText(str(self.dim_slider.value()))
        self.opacity_val.setText(str(self.opacity_slider.value()))
        self.frosted_cb.blockSignals(False)
        self.blur_slider.blockSignals(False)
        self.dim_slider.blockSignals(False)
        self.opacity_slider.blockSignals(False)
        self._update_preview(bg.get("image", ""))

    def _update_preview(self, path):
        if path and os.path.isfile(path):
            pix = QPixmap(path)
            if not pix.isNull():
                self.preview.setPixmap(pix.scaled(
                    self.preview.width(), self.preview.height(),
                    Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        self.preview.clear()
        self.preview.setText("预览")

    def _pick_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择背景图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.img_edit.setText(path)
            self._update_preview(path)
            self._on_appearance_change()

    def _reset_background(self):
        state.set_background({"enabled": False, "image": "", "blur": 24, "dim": 0, "panel_opacity": 65})
        self._load_background_ui()
        self.main.apply_appearance(force=True)

    def _force_render(self):
        self.main.apply_appearance(force=True)
        QMessageBox.information(self, "重新渲染", "背景已重新渲染")

    def _on_appearance_change(self):
        self.blur_val.setText(str(self.blur_slider.value()))
        self.dim_val.setText(str(self.dim_slider.value()))
        self.opacity_val.setText(str(self.opacity_slider.value()))
        state.set_background({
            "enabled": self.frosted_cb.isChecked(),
            "image": self.img_edit.text().strip(),
            "blur": self.blur_slider.value(),
            "dim": self.dim_slider.value(),
            "panel_opacity": self.opacity_slider.value(),
        })
        self.main.apply_appearance()

    # ================= 快捷键页 =================
    def _build_shortcuts_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(8)
        g = QGroupBox("快捷键（Windows 风格）")
        f = QVBoxLayout(g)
        table = QTableWidget(len(SHORTCUTS), 2)
        table.setHorizontalHeaderLabels(["功能", "快捷键"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        for i, (func, key) in enumerate(SHORTCUTS):
            table.setItem(i, 0, QTableWidgetItem(func))
            it = QTableWidgetItem(key)
            it.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 1, it)
        f.addWidget(table)
        tip = QLabel("提示：快捷键为固定绑定，符合 Windows 常用习惯。")
        tip.setStyleSheet("color:#8A94A6; font-size:11px;")
        f.addWidget(tip)
        lay.addWidget(g)
        lay.addStretch()
        return page
