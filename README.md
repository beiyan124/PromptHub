# 提示词管理器（Prompt Manager）

一个**本地优先**的 AI 提示词管理工具：VSCode 式布局 + JSON 结构化存储。
集中管理 LLM / 绘图 / 视频 / 音频四大门类的提示词（提示词片），支持多轮消息与嵌套结构。

## 功能特性

- **四门类 · 三层级**：文本 / 绘图 / 视频 / 音频 → 项目（文件夹）→ 提示词片（最小单位）
- **三种内容模式**：`plain` 纯文本 / `chat` 多轮消息（角色·内容行）/ `tree` 嵌套结构节点树
- **提示词片关联**：任意两片可建立双向关联（带说明），右侧面板可视化维护、一键跳转
- **VSCode 式布局**：左侧项目树（门类→项目→提示词片）、中间多标签编辑器、右侧设置与关联面板、底部状态栏门类切换
- **搜索过滤**：同时匹配项目名与提示词片名，命中自动展开所在项目
- **展开状态树持久化**：目录展开/折叠状态存盘，重启保持
- **主题系统**：亮 / 暗 / 灰三套主题 + 自定义主题色（8 种快捷浅色 + RGB 自由选择）
- **磨砂透明渲染**：可选图片背景，高斯模糊（纯 Python 计算，无第三方依赖）+ 遮罩 + 左中右面板透明度可调
- **数据可迁移**：存储地址可在设置中修改，自动搬运全部数据与层级（支持跨磁盘）
- **Windows 风格快捷键**：Ctrl+S / Ctrl+W / Ctrl+N / F2 / Delete / F5 / Ctrl+Tab 等 14 个
- **全面汉化**：界面、对话框、标准按钮均为中文

## 运行（开发环境）

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py        # 或双击 run.bat
```

## 打包为单文件 exe

```bash
.venv\Scripts\pip install pyinstaller pillow
build.bat                            # 自动合并图标 + 打包
# 产物：dist\提示词管理器.exe（35MB，含中文翻译与图标）
```

exe 双击即用，数据默认存放在 exe 同目录的 `PromtFile/` 文件夹（整个文件夹拷走 = 完整备份）。

## 目录结构

```
├── main.py                    # 入口（主题 / 中文翻译 / 窗口图标 / 主窗口）
├── app/
│   ├── config.py              # 配置：门类、路径（数据目录持久化、可迁移）
│   ├── models.py              # 数据层：JSON 读写 / 关联 / 项目与提示词片操作 / 迁移
│   ├── state.py               # 设置（config.json）与 UI 状态（展开树 .state.json）
│   ├── theme.py               # 主题引擎：三色板 + 主题色 + 磨砂 QSS
│   └── ui/                    # 界面组件
│       ├── main_window.py     # 主窗口：三区布局 + 门类切换 + 标签页 + 快捷键
│       ├── project_tree.py    # 项目树：三层结构 + 搜索过滤 + 展开状态记忆
│       ├── editor.py          # 编辑器：plain / chat / tree 三种视图
│       ├── right_panel.py     # 右侧面板：设置 + 关联管理
│       ├── link_dialog.py     # 设置关联对话框
│       ├── settings_dialog.py # 设置窗口（关于/存储/外观/快捷键）
│       └── background.py      # 磨砂背景层 + 纯 Python 高斯模糊
├── logo/                      # 应用图标（多尺寸 ico）
├── merge_icons.py             # 合并多尺寸图标脚本
├── prompt_manager.spec        # PyInstaller 打包配置
├── build.bat                  # 一键打包脚本
├── test_smoke.py              # 冒烟测试（offscreen）
└── docs/                      # 项目文档（重构记录 / 策划方案）
```

## 技术栈

Python 3.13 · PySide6 6.11 · JSON（纯本地存储，无数据库）· PyInstaller（打包）

## 数据模型

每个提示词片是一个 JSON 文件：`PromtFile/门类/项目/名称.json`，字段含
`id / title / description / category / project / format / content / links / created_at / updated_at`。
`links` 存相对路径 + 说明，实现双向关联。

## 贡献者

beiyan124 · workbuddy
