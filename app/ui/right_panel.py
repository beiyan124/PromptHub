# -*- coding: utf-8 -*-
"""右侧面板：提示词片设置（标题/描述/格式/元信息）+ 关联关系管理。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from .. import config
from .. import models
from .background import FrostedPanel
from .link_dialog import LinkDialog


class RightPanel(FrostedPanel):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.rel = None
        self.prompt = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)

        g1 = QGroupBox("提示词片设置")
        f = QVBoxLayout(g1)
        f.addWidget(QLabel("标题"))
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(lambda: self._on_prop_change("title"))
        f.addWidget(self.title_edit)
        f.addWidget(QLabel("描述"))
        self.desc_edit = QPlainTextEdit()
        self.desc_edit.setMaximumHeight(56)
        self.desc_edit.textChanged.connect(lambda: self._on_prop_change("desc"))
        f.addWidget(self.desc_edit)
        f.addWidget(QLabel("内容格式"))
        self.fmt_combo = QComboBox()
        for key, label in config.FORMATS:
            self.fmt_combo.addItem(label, key)
        self.fmt_combo.currentIndexChanged.connect(self._on_fmt_change)
        f.addWidget(self.fmt_combo)
        self.meta_lbl = QLabel("")
        self.meta_lbl.setWordWrap(True)
        self.meta_lbl.setStyleSheet("color:#8A94A6; font-size:11px;")
        f.addWidget(self.meta_lbl)
        lay.addWidget(g1)

        g2 = QGroupBox("关联关系")
        v = QVBoxLayout(g2)
        self.link_list = QListWidget()
        self.link_list.itemDoubleClicked.connect(self._jump)
        v.addWidget(self.link_list)
        row = QHBoxLayout()
        b_add = QPushButton("+ 设置关联")
        b_add.setObjectName("primary")
        b_del = QPushButton("删除选中")
        b_add.clicked.connect(self._add_link)
        b_del.clicked.connect(self._del_link)
        row.addWidget(b_add)
        row.addWidget(b_del)
        v.addLayout(row)
        tip = QLabel("关联双向可见，双击跳转")
        tip.setStyleSheet("color:#888780; font-size:11px;")
        v.addWidget(tip)
        lay.addWidget(g2)
        lay.addStretch()

        self._clear()

    # ---------- 状态 ----------
    def _clear(self):
        self.title_edit.blockSignals(True)
        self.desc_edit.blockSignals(True)
        self.fmt_combo.blockSignals(True)
        self.title_edit.clear()
        self.desc_edit.clear()
        self.meta_lbl.clear()
        self.link_list.clear()
        self.title_edit.blockSignals(False)
        self.desc_edit.blockSignals(False)
        self.fmt_combo.blockSignals(False)
        self.rel = None
        self.prompt = None

    def show_prompt(self, rel):
        self.rel = rel
        self.prompt = models.load_prompt(rel)
        self.title_edit.blockSignals(True)
        self.desc_edit.blockSignals(True)
        self.fmt_combo.blockSignals(True)
        self.title_edit.setText(self.prompt.get("title", ""))
        self.desc_edit.setPlainText(self.prompt.get("description", ""))
        idx = [k for k, _ in config.FORMATS].index(self.prompt.get("format", "plain"))
        self.fmt_combo.setCurrentIndex(idx)
        self.meta_lbl.setText(
            f"id: {self.prompt.get('id')}\n创建: {self.prompt.get('created_at')}\n更新: {self.prompt.get('updated_at')}"
        )
        self.title_edit.blockSignals(False)
        self.desc_edit.blockSignals(False)
        self.fmt_combo.blockSignals(False)
        self.refresh_links()

    def refresh_links(self):
        self.link_list.clear()
        if not self.prompt:
            return
        rel = self.rel
        for lk in models.get_out_links(self.prompt):
            self._add_link_item(f"{lk['target']}  → {lk.get('note') or lk.get('relation') or '关联'}", lk["target"])
        for lk in models.get_in_links(rel):
            self._add_link_item(f"来自: {lk['source']}  {lk.get('note') or ''}", lk["source"], inbound=True)

    def _add_link_item(self, text, rel, inbound=False):
        it = QListWidgetItem(text)
        it.setData(Qt.UserRole, rel)
        if inbound:
            it.setForeground(Qt.gray)
        self.link_list.addItem(it)

    # ---------- 操作 ----------
    def _on_prop_change(self, which):
        if not self.prompt:
            return
        tab = self.main.tab_for_rel(self.rel)
        if which == "title":
            self.prompt["title"] = self.title_edit.text()
        elif which == "desc":
            self.prompt["description"] = self.desc_edit.toPlainText()
        if tab:
            # 只同步标题/描述，不覆盖编辑器里未保存的内容
            tab.prompt["title"] = self.prompt["title"]
            tab.prompt["description"] = self.prompt["description"]
            tab.set_dirty(True)

    def _on_fmt_change(self):
        if not self.prompt:
            return
        fmt = self.fmt_combo.currentData()
        tab = self.main.tab_for_rel(self.rel)
        if tab:
            tab.switch_format(fmt)
            self.prompt.update(tab.prompt)
            self.meta_lbl.setText(
                f"id: {self.prompt.get('id')}\n创建: {self.prompt.get('created_at')}\n更新: {self.prompt.get('updated_at')}"
            )

    def _add_link(self):
        if not self.prompt:
            QMessageBox.information(self, "提示", "请先在编辑器打开一个提示词片")
            return
        dlg = LinkDialog(self, self.rel)
        if dlg.exec() == QDialog.Accepted:
            target = dlg.selected_rel()
            if target and models.add_link(self.prompt, target, dlg.note_text(), overwrite=True):
                models.save_prompt(self.prompt)
                self.main.on_prompt_saved(self.rel)
                self.refresh_links()
            else:
                QMessageBox.information(self, "提示", "该关联已存在")

    def _del_link(self):
        if not self.prompt:
            return
        it = self.link_list.currentItem()
        if it is None:
            return
        rel = it.data(Qt.UserRole)
        if rel is None:
            return
        models.remove_link(self.prompt, rel)
        models.save_prompt(self.prompt)
        self.main.on_prompt_saved(self.rel)
        self.refresh_links()

    def _jump(self, it):
        rel = it.data(Qt.UserRole)
        if rel:
            self.main.open_prompt(rel)
