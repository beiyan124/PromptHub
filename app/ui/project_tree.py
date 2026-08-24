# -*- coding: utf-8 -*-
"""项目树（侧边栏）：门类(根) → 项目 → 提示词片 三层结构，带右键菜单。

展开状态记忆：记录各项目节点的展开状态，rebuild 时恢复，
保证新建/重命名/删除提示词片等操作后目录结构展示不变。
"""

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMenu, QTreeWidget, QTreeWidgetItem, QStyle,
)

from .. import config
from .. import models
from .. import state


class ProjectTree(QTreeWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu)
        self.itemClicked.connect(self._on_click)
        self.itemDoubleClicked.connect(self._open)
        self.current_category = config.CATEGORIES[0]
        # 展开状态树：从磁盘恢复（重启后界面不变）
        self._expanded_map = state.get_expanded()
        self._filter_text = ""   # 搜索过滤关键字
        self._suppress_persist = False
        self.itemExpanded.connect(self._on_expand_change)
        self.itemCollapsed.connect(self._on_expand_change)
        self.rebuild()

    def _item_data(self, item):
        return item.data(0, Qt.UserRole) if item else None

    def _remember_expanded(self):
        """保存当前展开状态到内存（供本次 rebuild 恢复）。"""
        for i in range(self.topLevelItemCount()):
            cat_item = self.topLevelItem(i)
            cat = cat_item.text(0)
            self._expanded_map.setdefault(cat, {})
            for j in range(cat_item.childCount()):
                proj_item = cat_item.child(j)
                self._expanded_map[cat][proj_item.text(0)] = proj_item.isExpanded()

    def _on_expand_change(self, item):
        """用户手动展开/折叠时持久化状态树。"""
        if not self._suppress_persist:
            self._persist_expanded()

    def _persist_expanded(self):
        """把当前展开状态树写入磁盘（.state.json），重启后恢复。"""
        expanded = {}
        for i in range(self.topLevelItemCount()):
            cat_item = self.topLevelItem(i)
            cat = cat_item.text(0)
            expanded[cat] = {}
            for j in range(cat_item.childCount()):
                proj_item = cat_item.child(j)
                expanded[cat][proj_item.text(0)] = proj_item.isExpanded()
        state.set_expanded(expanded)

    def rebuild(self):
        """重建树；重建前记忆展开状态，重建后恢复（保证操作后结构不变）。"""
        self._remember_expanded()
        self._suppress_persist = True
        self.clear()
        dir_icon = self.style().standardIcon(QStyle.SP_DirIcon)
        file_icon = self.style().standardIcon(QStyle.SP_FileIcon)
        c = self.current_category
        cat_item = QTreeWidgetItem([c])
        cat_item.setData(0, Qt.UserRole, {"kind": "category", "category": c})
        cat_item.setIcon(0, dir_icon)
        for proj in models.list_projects(c):
            proj_item = QTreeWidgetItem([proj])
            proj_item.setData(0, Qt.UserRole, {"kind": "project", "category": c, "project": proj})
            proj_item.setIcon(0, dir_icon)
            for title in models.list_prompts(c, proj):
                it = QTreeWidgetItem([title])
                it.setData(0, Qt.UserRole, {"kind": "prompt", "rel": models.prompt_rel(c, proj, title)})
                it.setIcon(0, file_icon)
                proj_item.addChild(it)
            cat_item.addChild(proj_item)
        self.addTopLevelItem(cat_item)
        cat_item.setExpanded(True)
        # 树挂载完成后恢复各项目的展开状态（挂载前 setExpanded 不生效）
        for j in range(cat_item.childCount()):
            proj_item = cat_item.child(j)
            proj_item.setExpanded(self._expanded_map.get(c, {}).get(proj_item.text(0), True))
        self._suppress_persist = False
        if self._filter_text:
            self._apply_filter()

    # ---------- 搜索过滤 ----------
    def set_filter(self, text):
        """设置搜索关键字并重建树（匹配：提示词片名 / 项目名 / 门类名）。"""
        self._filter_text = (text or "").strip().lower()
        self.rebuild()

    def _apply_filter(self):
        """过滤树：命中提示词片/项目/门类时显示，并自动展开命中项所在项目。"""
        kw = self._filter_text
        for i in range(self.topLevelItemCount()):
            cat_item = self.topLevelItem(i)
            cat_match = kw in cat_item.text(0).lower()
            any_visible = False
            for j in range(cat_item.childCount()):
                proj_item = cat_item.child(j)
                proj_match = kw in proj_item.text(0).lower()
                proj_visible = proj_match
                if proj_match:
                    # 项目名命中 → 显示全部提示词片并展开
                    for k in range(proj_item.childCount()):
                        proj_item.child(k).setHidden(False)
                    proj_item.setExpanded(True)
                else:
                    for k in range(proj_item.childCount()):
                        leaf = proj_item.child(k)
                        leaf_match = kw in leaf.text(0).lower()
                        leaf.setHidden(not leaf_match)
                        proj_visible = proj_visible or leaf_match
                    # 有提示词片命中 → 自动展开所在项目
                    if proj_visible:
                        proj_item.setExpanded(True)
                proj_item.setHidden(not proj_visible)
                any_visible = any_visible or proj_visible
            cat_item.setHidden(not (cat_match or any_visible))
            if any_visible or cat_match:
                cat_item.setExpanded(True)

    def expand_all(self):
        self.expandAll()

    def collapse_all(self):
        self.collapseAll()

    def _on_click(self, item, col):
        d = self._item_data(item)
        if not d:
            return
        if d["kind"] == "prompt":
            self.main.open_prompt(d["rel"])

    def _open(self, item, col):
        d = self._item_data(item)
        if d and d.get("kind") == "prompt":
            self.main.open_prompt(d["rel"])

    def _menu(self, pos):
        item = self.itemAt(pos)
        if item is None:
            return
        d = self._item_data(item)
        if not d:
            return
        menu = self._make_menu(d)
        menu.exec(self.viewport().mapToGlobal(pos))

    def _make_menu(self, d):
        menu = QMenu(self)
        kind = d["kind"]
        menu.addAction("展开全部").triggered.connect(self.expand_all)
        menu.addAction("最小化全部").triggered.connect(self.collapse_all)
        menu.addSeparator()
        if kind == "category":
            menu.addAction("新建项目").triggered.connect(lambda: self.main.new_project(d["category"]))
        elif kind == "project":
            c, p = d["category"], d["project"]
            menu.addAction("新建提示词片").triggered.connect(lambda: self.main.new_prompt_dialog(c, p))
            menu.addSeparator()
            menu.addAction("重命名项目").triggered.connect(lambda: self.main.rename_project_dialog(c, p))
            menu.addAction("删除项目").triggered.connect(lambda: self.main.delete_project_dialog(c, p))
            menu.addAction("在资源管理器中打开").triggered.connect(
                lambda: self.main.open_in_explorer(os.path.join(config.DATA_DIR, c, p)))
        else:
            rel = d["rel"]
            c, p, t = models.rel_parts(rel)
            menu.addAction("打开").triggered.connect(lambda: self.main.open_prompt(rel))
            menu.addAction("复制到…").triggered.connect(lambda: self.main.copy_prompt_dialog(rel))
            menu.addSeparator()
            menu.addAction("重命名").triggered.connect(lambda: self.main.rename_prompt_dialog(c, p, t))
            menu.addAction("删除").triggered.connect(lambda: self.main.delete_prompt_dialog(rel))
            menu.addSeparator()
            menu.addAction("在资源管理器中打开").triggered.connect(
                lambda: self.main.open_in_explorer(os.path.dirname(models.prompt_abs_path(rel))))
        return menu
