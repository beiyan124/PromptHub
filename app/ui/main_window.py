# -*- coding: utf-8 -*-
"""主窗口：VSCode 式五区布局（活动栏 / 侧边栏 / 多标签编辑器 / 右侧面板 / 状态栏）。"""

import os

from PySide6.QtCore import QEvent, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QSplitter, QTabWidget, QToolButton,
    QVBoxLayout, QWidget,
)

from .. import config
from .. import models
from .. import state
from .. import theme
from .background import BlurBackground, FrostedPanel
from .editor import EditorTab
from .link_dialog import LinkDialog
from .project_tree import ProjectTree
from .right_panel import RightPanel
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        models.ensure_data()
        self.setWindowTitle(config.APP_NAME)
        self.resize(1180, 720)

        # 中央分割：活动栏 | 侧边栏(树+底部按钮) | 编辑器 | 右侧面板
        splitter = QSplitter(Qt.Horizontal)

        self.tree = ProjectTree(self)
        # 左侧栏：搜索框 + 三层树 + 底部操作按钮（Cubase 风格 ＋/－），磨砂半透明容器
        side = FrostedPanel()
        side.setObjectName("SidePanel")
        side_lay = QVBoxLayout(side)
        side_lay.setContentsMargins(0, 0, 0, 0)
        side_lay.setSpacing(0)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索项目 / 提示词片…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self.tree.set_filter)
        side_lay.addWidget(self.search_edit)
        side_lay.addWidget(self.tree, 1)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(6, 6, 6, 6)
        btn_row.setSpacing(4)
        self.btn_new_proj = QToolButton()
        self.btn_new_proj.setText("＋ 项目")
        self.btn_new_proj.setToolTip("在当前门类下新建项目")
        self.btn_new_proj.clicked.connect(lambda: self.new_project(self.tree.current_category))
        self.btn_new_prompt = QToolButton()
        self.btn_new_prompt.setText("＋ 提示词片")
        self.btn_new_prompt.setToolTip("在选中的项目下新建提示词片")
        self.btn_new_prompt.clicked.connect(self.new_prompt_under_selected)
        self.btn_del = QToolButton()
        self.btn_del.setText("－")
        self.btn_del.setObjectName("del_btn")
        self.btn_del.setToolTip("删除选中的项目或提示词片")
        self.btn_del.clicked.connect(self.delete_selected)
        btn_row.addWidget(self.btn_new_proj)
        btn_row.addWidget(self.btn_new_prompt)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_del)
        side_lay.addLayout(btn_row)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.right = RightPanel(self)
        self.right.setObjectName("RightPanel")

        # 编辑器区域容器（磨砂半透明容器）
        editor_wrap = FrostedPanel()
        editor_wrap.setObjectName("EditorArea")
        el = QVBoxLayout(editor_wrap)
        el.setContentsMargins(0, 0, 0, 0)
        el.setSpacing(0)
        el.addWidget(self.tabs)

        splitter.addWidget(side)
        splitter.addWidget(editor_wrap)
        splitter.addWidget(self.right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([240, 640, 280])
        # 左中右三个磨砂面板（面板透明度调节目标）
        self._panels = [side, editor_wrap, self.right]

        # 中央层叠：磨砂背景层（最底）+ 内容层
        root = QWidget()
        self.background = BlurBackground(root)
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(splitter, 1)
        self.setCentralWidget(root)
        self.background.lower()
        self.background.setGeometry(root.rect())
        self._frosted = False
        QApplication.instance().installEventFilter(self)
        self.apply_appearance()

        # 状态栏：左下角 = 设置 + 四个门类
        sb = self.statusBar()
        b_set_sb = QToolButton()
        b_set_sb.setText("⚙ 设置")
        b_set_sb.setToolButtonStyle(Qt.ToolButtonTextOnly)
        b_set_sb.clicked.connect(self.show_settings)
        sb.addWidget(b_set_sb)
        self.cat_btns = QButtonGroup(self)
        self.cat_btns.setExclusive(True)
        for i, c in enumerate(config.CATEGORIES):
            btn = QToolButton()
            btn.setText(c)
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
            btn.clicked.connect(lambda _=False, cat=c: self.switch_category(cat))
            self.cat_btns.addButton(btn, i)
            sb.addWidget(btn)
        self.status_lbl = QLabel("就绪")
        sb.addPermanentWidget(self.status_lbl)
        self.switch_category(config.CATEGORIES[0])

        # Ctrl+S 保存当前标签
        act = QAction(self)
        act.setShortcut(QKeySequence.Save)
        act.triggered.connect(self.save_current)
        self.addAction(act)
        # Ctrl+W 关闭当前标签
        act2 = QAction(self)
        act2.setShortcut(QKeySequence("Ctrl+W"))
        act2.triggered.connect(self._close_current_tab)
        self.addAction(act2)

        # ---- Windows 风格快捷键 ----
        def add_shortcut(keys, slot):
            a = QAction(self)
            a.setShortcut(QKeySequence(keys))
            a.triggered.connect(slot)
            self.addAction(a)
            return a

        add_shortcut("Ctrl+N", self.new_prompt_under_selected)      # 新建提示词片
        add_shortcut("Ctrl+Shift+N", lambda: self.new_project(self.tree.current_category))  # 新建项目
        add_shortcut("Ctrl+F", self._focus_search)                  # 聚焦搜索
        add_shortcut("Ctrl+Shift+S", self.save_all)                 # 保存全部
        add_shortcut("F2", self.rename_selected)                    # 重命名选中
        add_shortcut("Delete", self.delete_selected)                # 删除选中
        add_shortcut("F5", lambda: self.refresh_tree())             # 刷新目录
        add_shortcut("Ctrl+Shift+R", lambda: self.apply_appearance(force=True))  # 重新渲染
        add_shortcut("Ctrl+Tab", lambda: self._switch_tab(1))       # 下一个标签
        add_shortcut("Ctrl+Shift+Tab", lambda: self._switch_tab(-1))  # 上一个标签
        add_shortcut("Ctrl+,", self.show_settings)                  # 打开设置
        add_shortcut("Ctrl+Q", self.close)                          # 退出

    def _focus_search(self):
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def save_all(self):
        """保存全部已打开标签。"""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, EditorTab) and tab.dirty:
                tab.save()
        self.set_status("已保存全部")

    def rename_selected(self):
        """F2 重命名树中选中的项目或提示词片。"""
        d = self.current_selected_data()
        if not d:
            return
        if d["kind"] == "project":
            self.rename_project_dialog(d["category"], d["project"])
        elif d["kind"] == "prompt":
            c, p, t = models.rel_parts(d["rel"])
            self.rename_prompt_dialog(c, p, t)

    def _switch_tab(self, step):
        n = self.tabs.count()
        if n <= 1:
            return
        self.tabs.setCurrentIndex((self.tabs.currentIndex() + step) % n)

    # ---------- 门类 / 树 ----------
    def switch_category(self, cat):
        self.tree.current_category = cat
        self.tree.rebuild()
        self.set_status(f"门类：{cat}")

    def set_status(self, text):
        self.status_lbl.setText(text)

    def refresh_tree(self):
        self.tree.rebuild()

    def current_selected_data(self):
        """树中当前选中项的数据 dict，无选中返回 None。"""
        items = self.tree.selectedItems()
        if not items:
            return None
        return self.tree._item_data(items[0])

    # ---------- 标签页 ----------
    def tab_for_rel(self, rel):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if getattr(tab, "rel", None) == rel:
                return tab
        return None

    def open_prompt(self, rel):
        tab = self.tab_for_rel(rel)
        if tab:
            self.tabs.setCurrentWidget(tab)
        else:
            tab = EditorTab(self, rel)
            self.tabs.addTab(tab, models.rel_parts(rel)[-1][:-5])
            self.tabs.setTabToolTip(self.tabs.count() - 1, rel)
            self.tabs.setCurrentWidget(tab)
        self.right.show_prompt(rel)
        self.set_status(f"打开：{rel}")

    def save_current(self):
        tab = self.tabs.currentWidget()
        if isinstance(tab, EditorTab):
            tab.save()
            self.right.show_prompt(tab.rel)

    def on_prompt_saved(self, rel):
        self.refresh_tree()

    def _tab_changed(self, idx):
        tab = self.tabs.widget(idx) if idx >= 0 else None
        if isinstance(tab, EditorTab):
            self.right.show_prompt(tab.rel)

    def _close_current_tab(self):
        i = self.tabs.currentIndex()
        if i >= 0:
            self._close_tab(i)

    def _close_tab(self, idx):
        tab = self.tabs.widget(idx)
        if isinstance(tab, EditorTab) and tab.dirty:
            r = QMessageBox.question(self, "未保存", f"「{tab.prompt.get('title')}」有未保存的修改，要保存吗？",
                                     QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if r == QMessageBox.Cancel:
                return
            if r == QMessageBox.Save:
                tab.save()
        self.tabs.removeTab(idx)

    # ---------- 项目 / 提示词片 操作 ----------
    def new_project(self, category):
        name, ok = QInputDialog.getText(self, "新建项目", f"在「{category}」下新建项目：")
        if not ok or not name.strip():
            return
        ok2, msg = models.create_project(category, name.strip())
        if not ok2:
            QMessageBox.warning(self, "提示", msg)
            return
        self.refresh_tree()
        self._select_project_in_tree(category, name.strip())
        self.set_status(f"已创建项目「{name.strip()}」，点左侧 ＋提示词片 创建内容")

    def _select_project_in_tree(self, category, project):
        """树中定位并高亮指定项目。"""
        for i in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(i)
            if root.text(0) != category:
                continue
            for j in range(root.childCount()):
                if root.child(j).text(0) == project:
                    root.setExpanded(True)
                    self.tree.setCurrentItem(root.child(j))
                    return

    def rename_project_dialog(self, category, old):
        new, ok = QInputDialog.getText(self, "重命名项目", "新名称：", text=old)
        if not ok or not new.strip() or new.strip() == old:
            return
        ok2, msg = models.rename_project(category, old, new.strip())
        if not ok2:
            QMessageBox.warning(self, "提示", msg)
            return
        self.refresh_tree()
        self._select_project_in_tree(category, new.strip())
        self.set_status(f"已重命名：{old} → {new.strip()}")

    def delete_project_dialog(self, category, name):
        r = QMessageBox.question(self, "确认删除", f"将把项目「{name}」连同其中全部提示词片移入回收站，确定？",
                                 QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            prefix = f"{category}/{name}/"
            for i in range(self.tabs.count() - 1, -1, -1):
                tab = self.tabs.widget(i)
                if isinstance(tab, EditorTab) and tab.rel.startswith(prefix):
                    self.tabs.removeTab(i)
            models.delete_project(category, name)
            self.refresh_tree()
            self.set_status(f"已删除项目：{name}")

    def new_prompt_dialog(self, category, project):
        title, ok = QInputDialog.getText(self, "新建提示词片", f"在「{project}」中新建提示词片：")
        if not ok or not title.strip():
            return
        ok2, msg = models.create_prompt(category, project, title.strip())
        if not ok2:
            QMessageBox.warning(self, "提示", msg)
        else:
            self.refresh_tree()
            self.open_prompt(models.prompt_rel(category, project, title.strip()))

    def rename_prompt_dialog(self, category, project, old):
        new, ok = QInputDialog.getText(self, "重命名提示词片", "新名称：", text=old)
        if not ok or not new.strip() or new.strip() == old:
            return
        old_rel = models.prompt_rel(category, project, old)
        ok2, msg = models.rename_prompt(category, project, old, new.strip())
        if not ok2:
            QMessageBox.warning(self, "提示", msg)
            return
        tab = self.tab_for_rel(old_rel)
        if tab:
            tab.rel = models.prompt_rel(category, project, new.strip())
            tab.prompt["title"] = new.strip()
            tab.set_dirty(False)
        self.refresh_tree()
        self.set_status(f"已重命名：{old} → {new.strip()}")

    def delete_prompt_dialog(self, rel):
        r = QMessageBox.question(self, "确认删除", f"将把「{rel}」移入回收站，确定？",
                                 QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            idx = self.tabs.indexOf(self.tab_for_rel(rel))
            if idx >= 0:
                self.tabs.removeTab(idx)
            models.delete_prompt(rel)
            self.refresh_tree()
            self.right._clear()
            self.set_status(f"已删除：{rel}")

    def copy_prompt_dialog(self, rel):
        dlg = LinkDialog(self, rel)
        dlg.setWindowTitle("复制到…")
        dlg.note.setPlaceholderText("目标名称（留空则自动加“副本”）")
        if dlg.exec() != QDialog.Accepted:
            return
        target_rel = dlg.selected_rel()
        if not target_rel:
            return
        tc, tp, _ = models.rel_parts(target_rel)
        new_title = dlg.note_text() or f"{models.rel_parts(rel)[-1][:-5]} 副本"
        ok, msg = models.copy_prompt(rel, tc, tp, new_title)
        if not ok:
            QMessageBox.warning(self, "提示", msg)
        else:
            self.refresh_tree()
            self.set_status(f"已复制到：{tc}/{tp}/{new_title}")

    # ---------- 左侧栏底部按钮（Cubase 风格 ＋/－） ----------
    def new_prompt_under_selected(self):
        """在树选中的项目下新建提示词片；未选中项目时智能取第一个项目。"""
        d = self.current_selected_data()
        if d and d["kind"] == "project":
            self.new_prompt_dialog(d["category"], d["project"])
            return
        if d and d["kind"] == "prompt":
            c, p, _ = models.rel_parts(d["rel"])
            self.new_prompt_dialog(c, p)
            return
        projects = models.list_projects(self.tree.current_category)
        if projects:
            self.new_prompt_dialog(self.tree.current_category, projects[0])
        else:
            QMessageBox.information(self, "提示", "请先点「＋ 项目」创建一个项目")

    def delete_selected(self):
        """删除树中选中的项目或提示词片（带确认）。"""
        d = self.current_selected_data()
        if not d:
            return
        if d["kind"] == "project":
            self.delete_project_dialog(d["category"], d["project"])
        elif d["kind"] == "prompt":
            self.delete_prompt_dialog(d["rel"])

    def open_in_explorer(self, path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    # ---------- 外观（主题 + 磨砂背景） ----------
    def apply_appearance(self, force=False):
        """根据状态应用主题（亮/暗/灰 + 主题色）与磨砂背景。force=True 强制重新渲染。"""
        bg = state.get_background()
        t = state.get_theme()
        self._frosted = bool(bg.get("enabled", False))
        self.background.apply(bg, force=force)
        # 左中右面板底色随主题（dark/gray=浅棕黑，light=浅亮白）；
        # alpha 仍由「面板透明度」滑块控制（透明度逻辑不变）
        opacity = int(bg.get("panel_opacity", 65))
        alpha = int(255 * opacity / 100)
        r, g, b = theme.panel_bar(t.get("name", "dark"))
        for p in getattr(self, "_panels", []):
            p.set_frost_color(r, g, b, alpha)
        QApplication.instance().setStyleSheet(
            theme.build_qss(self._frosted, t.get("name", "dark"), t.get("accent", "#1E5EFF")))

    def eventFilter(self, obj, ev):
        """磨砂模式下，把所有非顶层控件（含动态创建的标签页等）设为透明背景，
        使 QSS 半透明面板能真正透出底层模糊背景图。"""
        if self._frosted and ev.type() == QEvent.PolishRequest:
            if isinstance(obj, QWidget) and obj.window() is not obj:
                obj.setAttribute(Qt.WA_TranslucentBackground, True)
        return super().eventFilter(obj, ev)

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if hasattr(self, "background"):
            self.background.setGeometry(self.centralWidget().rect())

    # ---------- 设置 ----------
    def show_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def on_data_dir_changed(self):
        """数据目录迁移完成后刷新全部界面。"""
        self.refresh_tree()
        self.set_status(f"数据目录已迁移：{config.DATA_DIR}")

    def closeEvent(self, ev):
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, EditorTab) and tab.dirty:
                r = QMessageBox.question(self, "未保存", f"「{tab.prompt.get('title')}」有未保存的修改，要保存吗？",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                if r == QMessageBox.Cancel:
                    ev.ignore()
                    return
                if r == QMessageBox.Save:
                    tab.save()
        ev.accept()
