# -*- coding: utf-8 -*-
"""设置关联对话框：树形选择目标提示词片 + 关联说明。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QLineEdit, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from .. import config
from .. import models


class LinkDialog(QDialog):
    def __init__(self, parent, exclude_rel):
        super().__init__(parent)
        self.setWindowTitle("设置关联")
        self.resize(720, 840)  # 默认更大（相对原 360x420 放大一倍）
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("选择要关联的提示词片："))
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索提示词片名称…")
        self.search.textChanged.connect(self._filter)
        lay.addWidget(self.search)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["提示词片"])
        self._build_tree(exclude_rel)
        lay.addWidget(self.tree)
        lay.addWidget(QLabel("关联说明（可选）："))
        self.note = QLineEdit()
        self.note.setPlaceholderText("如：组合使用 / 先审后诉 / 参考模板")
        lay.addWidget(self.note)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._ok)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _build_tree(self, exclude_rel):
        self.tree.clear()
        for c in config.CATEGORIES:
            cat_item = QTreeWidgetItem([c])
            cat_item.setFlags(Qt.ItemIsEnabled)
            for proj in models.list_projects(c):
                proj_item = QTreeWidgetItem([proj])
                proj_item.setFlags(Qt.ItemIsEnabled)
                for title in models.list_prompts(c, proj):
                    rel = models.prompt_rel(c, proj, title)
                    if rel == exclude_rel:
                        continue
                    it = QTreeWidgetItem([f"{title}.json"])
                    it.setData(0, Qt.UserRole, rel)
                    proj_item.addChild(it)
                cat_item.addChild(proj_item)
            self.tree.addTopLevelItem(cat_item)
        self.tree.expandAll()

    def _filter(self, text):
        text = text.strip().lower()
        for ci in range(self.tree.topLevelItemCount()):
            cat_item = self.tree.topLevelItem(ci)
            cat_match = False
            for pj in range(cat_item.childCount()):
                proj_item = cat_item.child(pj)
                proj_match = False
                for pi in range(proj_item.childCount()):
                    leaf = proj_item.child(pi)
                    match = (not text) or (text in leaf.text(0).lower())
                    leaf.setHidden(not match)
                    proj_match = proj_match or match
                proj_item.setHidden(not (proj_match or (text and text in proj_item.text(0).lower())))
                cat_match = cat_match or (not proj_item.isHidden())
            cat_item.setHidden(not (cat_match or (text and text in cat_item.text(0).lower())))

    def _ok(self):
        items = self.tree.selectedItems()
        if not items or not items[0].data(0, Qt.UserRole):
            QMessageBox.warning(self, "提示", "请选择一个提示词片")
            return
        self.accept()

    def selected_rel(self):
        items = self.tree.selectedItems()
        return items[0].data(0, Qt.UserRole) if items else None

    def note_text(self):
        return self.note.text().strip()
