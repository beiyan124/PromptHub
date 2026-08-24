# -*- coding: utf-8 -*-
"""编辑器标签页：支持 plain（纯文本）/ chat（多轮消息）/ tree（嵌套结构）三种内容模式。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
    QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QHeaderView,
)

from .. import config
from .. import models


class EditorTab(QWidget):
    def __init__(self, main, rel):
        super().__init__()
        self.main = main
        self.rel = rel
        self.prompt = models.load_prompt(rel)
        self.dirty = False
        self._loading = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)

        top = QHBoxLayout()
        path_lbl = QLabel(rel)
        path_lbl.setStyleSheet("color:#8A94A6; font-size:11px;")
        save_btn = QPushButton("保存 (Ctrl+S)")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self.save)
        save_btn.setFixedHeight(26)
        top.addWidget(path_lbl)
        top.addStretch()
        top.addWidget(save_btn)
        lay.addLayout(top)

        # plain 编辑器
        self.plain_edit = QPlainTextEdit()
        self.plain_edit.textChanged.connect(lambda: self._on_change())
        # chat 编辑器
        self.chat_table = QTableWidget(0, 2)
        self.chat_table.setHorizontalHeaderLabels(["角色", "内容"])
        self.chat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.chat_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.chat_table.verticalHeader().setDefaultSectionSize(70)
        chat_btns = QHBoxLayout()
        b_add = QPushButton("+ 添加消息")
        b_del = QPushButton("删除选中")
        b_add.clicked.connect(self._chat_add)
        b_del.clicked.connect(self._chat_del)
        chat_btns.addWidget(b_add)
        chat_btns.addWidget(b_del)
        chat_btns.addStretch()
        chat_wrap = QWidget()
        cl = QVBoxLayout(chat_wrap)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.addWidget(self.chat_table)
        cl.addLayout(chat_btns)
        # tree 编辑器
        tree_btns = QHBoxLayout()
        tb_add = QPushButton("+ 添加子节点")
        tb_del = QPushButton("删除节点")
        tb_apply = QPushButton("应用修改")
        tb_add.clicked.connect(self._tree_add)
        tb_del.clicked.connect(self._tree_del)
        tb_apply.clicked.connect(self._tree_apply)
        tree_btns.addWidget(tb_add)
        tree_btns.addWidget(tb_del)
        tree_btns.addWidget(tb_apply)
        tree_btns.addStretch()
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["类型", "内容"])
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree_widget.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree_widget.itemSelectionChanged.connect(self._tree_select)
        self.tree_type = QLineEdit()
        self.tree_type.setPlaceholderText("节点类型，如：主任务 / 子任务 / 约束")
        self.tree_content = QPlainTextEdit()
        self.tree_content.setMaximumHeight(110)
        self.tree_content.textChanged.connect(lambda: self._on_change())
        self.tree_type.textChanged.connect(lambda: self._on_change())
        tree_edit_lay = QVBoxLayout()
        tree_edit_lay.addWidget(self.tree_type)
        tree_edit_lay.addWidget(self.tree_content)
        tree_wrap = QWidget()
        tl = QVBoxLayout(tree_wrap)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.addWidget(self.tree_widget, 3)
        tl.addLayout(tree_btns)
        tl.addLayout(tree_edit_lay, 2)

        # 统一放到 QStackedWidget（plain/chat/tree 三种编辑视图）
        self.stack = QStackedWidget()
        self.stack.addWidget(self.plain_edit)
        self.stack.addWidget(chat_wrap)
        self.stack.addWidget(tree_wrap)
        lay.addWidget(self.stack, 1)

        self._load_from_prompt()

    # ---------- 内容加载 / 提取 ----------
    def _load_from_prompt(self):
        self._loading = True
        fmt = self.prompt.get("format", "plain")
        self.stack.setCurrentIndex(["plain", "chat", "tree"].index(fmt) if fmt in ("plain", "chat", "tree") else 0)
        if fmt == "plain":
            self.plain_edit.setPlainText(self.prompt.get("content") or "")
        elif fmt == "chat":
            self.chat_table.setRowCount(0)
            for m in (self.prompt.get("content") or []):
                self._chat_add_row(m.get("role", "user"), m.get("content", ""))
        elif fmt == "tree":
            self._tree_load(self.prompt.get("content") or {"type": "根任务", "content": "", "children": []})
        self._loading = False
        self.set_dirty(False)

    def _collect(self):
        fmt = self.prompt.get("format", "plain")
        if fmt == "plain":
            return self.plain_edit.toPlainText()
        if fmt == "chat":
            msgs = []
            for i in range(self.chat_table.rowCount()):
                cb = self.chat_table.cellWidget(i, 0)
                ed = self.chat_table.cellWidget(i, 1)
                if ed is None:
                    continue
                role = cb.currentData() if cb else "user"
                content = ed.toPlainText()
                if content.strip() or role:
                    msgs.append({"role": role, "content": content})
            return msgs
        # tree
        root_item = self.tree_widget.topLevelItem(0)
        if root_item is None:
            return {"type": "根任务", "content": "", "children": []}
        return self._tree_item_to_dict(root_item)

    def _apply(self):
        self.prompt["content"] = self._collect()

    def save(self):
        self._apply()
        models.save_prompt(self.prompt)
        self.set_dirty(False)
        self.main.on_prompt_saved(self.rel)

    def switch_format(self, fmt):
        if fmt == self.prompt.get("format", "plain"):
            return
        old = self.prompt.get("format", "plain")
        text = models.content_to_text(self._collect(), old)
        self.prompt["format"] = fmt
        self.prompt["content"] = models.text_to_content(text, fmt)
        self._load_from_prompt()
        self.set_dirty(True)

    # ---------- 脏标记 ----------
    def _on_change(self):
        if not self._loading:
            self.set_dirty(True)

    def set_dirty(self, dirty):
        self.dirty = dirty
        idx = self.main.tabs.indexOf(self)
        if idx >= 0:
            title = ("● " if dirty else "") + self.prompt.get("title", "?")
            self.main.tabs.setTabText(idx, title)
            self.main.tabs.setTabToolTip(idx, self.rel)

    # ---------- chat 模式 ----------
    def _chat_add_row(self, role="user", content=""):
        r = self.chat_table.rowCount()
        self.chat_table.insertRow(r)
        cb = QComboBox()
        # 显示中文角色名，数据存英文值（JSON 兼容）
        for val in config.CHAT_ROLES:
            cb.addItem(config.CHAT_ROLE_LABELS.get(val, val), val)
        cb.setCurrentIndex(cb.findData(role) if role in config.CHAT_ROLES else 0)
        cb.currentIndexChanged.connect(lambda: self._on_change())
        ed = QPlainTextEdit()
        ed.setPlainText(content)
        ed.textChanged.connect(lambda: self._on_change())
        self.chat_table.setCellWidget(r, 0, cb)
        self.chat_table.setCellWidget(r, 1, ed)
        self._on_change()

    def _chat_add(self):
        self._chat_add_row()

    def _chat_del(self):
        rows = sorted({i.row() for i in self.chat_table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.chat_table.removeRow(r)
        self._on_change()

    # ---------- tree 模式 ----------
    def _tree_load(self, root):
        self.tree_widget.clear()
        item = self._tree_dict_to_item(root)
        self.tree_widget.addTopLevelItem(item)
        item.setExpanded(True)

    def _tree_dict_to_item(self, node):
        item = QTreeWidgetItem([node.get("type", ""), (node.get("content") or "").replace("\n", " ")])
        item.setData(0, Qt.UserRole, node)
        for ch in node.get("children", []):
            item.addChild(self._tree_dict_to_item(ch))
        return item

    def _tree_item_to_dict(self, item):
        node = item.data(0, Qt.UserRole) or {"type": "", "content": "", "children": []}
        node["children"] = []
        for i in range(item.childCount()):
            node["children"].append(self._tree_item_to_dict(item.child(i)))
        return node

    def _tree_select(self):
        items = self.tree_widget.selectedItems()
        if not items:
            return
        node = items[0].data(0, Qt.UserRole) or {}
        self._loading = True
        self.tree_type.setText(node.get("type", ""))
        self.tree_content.setPlainText(node.get("content", ""))
        self._loading = False

    def _tree_apply(self):
        items = self.tree_widget.selectedItems()
        if not items:
            QMessageBox.information(self, "提示", "请先在树中选中一个节点")
            return
        node = items[0].data(0, Qt.UserRole) or {}
        node["type"] = self.tree_type.text()
        node["content"] = self.tree_content.toPlainText()
        items[0].setText(0, node["type"])
        items[0].setText(1, node["content"].replace("\n", " "))
        self._on_change()

    def _tree_add(self):
        parent = self.tree_widget.selectedItems()[0] if self.tree_widget.selectedItems() else None
        node = {"type": "子任务", "content": "", "children": []}
        item = self._tree_dict_to_item(node)
        if parent is None:
            self.tree_widget.addTopLevelItem(item)
        else:
            parent.addChild(item)
            parent.setExpanded(True)
        self.tree_widget.setCurrentItem(item)
        self._on_change()

    def _tree_del(self):
        items = self.tree_widget.selectedItems()
        if not items:
            return
        if items[0] == self.tree_widget.topLevelItem(0) and items[0].childCount() == 0:
            QMessageBox.information(self, "提示", "根节点不能删除")
            return
        parent = items[0].parent()
        if parent is None:
            self.tree_widget.takeTopLevelItem(self.tree_widget.indexOfTopLevelItem(items[0]))
        else:
            parent.removeChild(items[0])
        self._on_change()
