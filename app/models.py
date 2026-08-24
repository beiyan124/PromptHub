# -*- coding: utf-8 -*-
"""数据层：JSON 存储读写、关联关系、项目/提示词片操作、内容模式转换。

所有路径基于 config.DATA_DIR（可在设置中修改，修改后数据自动搬运）。
"""

import json
import os
import shutil
import uuid
from datetime import datetime

from . import config

# ---------------------------------------------------------------------------
# JSON 读写
# ---------------------------------------------------------------------------
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_data():
    """首次运行创建 data 目录结构。"""
    for c in config.CATEGORIES:
        os.makedirs(os.path.join(config.DATA_DIR, c), exist_ok=True)
    os.makedirs(config.trash_dir(), exist_ok=True)


def prompt_rel(category, project, title):
    """提示词片的相对路径（相对 data/，跨平台用 /）。"""
    return f"{category}/{project}/{title}.json"


def rel_parts(rel):
    return rel.replace("\\", "/").split("/")


def prompt_abs_path(rel):
    return os.path.join(config.DATA_DIR, *rel_parts(rel))


def list_projects(category):
    d = os.path.join(config.DATA_DIR, category)
    if not os.path.isdir(d):
        return []
    return sorted(x for x in os.listdir(d) if os.path.isdir(os.path.join(d, x)))


def list_prompts(category, project):
    d = os.path.join(config.DATA_DIR, category, project)
    if not os.path.isdir(d):
        return []
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def iter_all_prompts():
    """遍历全部提示词片，产出 (category, project, title, rel)。"""
    for c in config.CATEGORIES:
        for proj in list_projects(c):
            for title in list_prompts(c, proj):
                yield c, proj, title, prompt_rel(c, proj, title)


def new_prompt(category, project, title):
    return {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "description": "",
        "category": category,
        "project": project,
        "format": "plain",
        "content": "",
        "links": [],
        "created_at": now_str(),
        "updated_at": now_str(),
    }


def load_prompt(rel):
    with open(prompt_abs_path(rel), encoding="utf-8") as f:
        return json.load(f)


def save_prompt(p):
    p["updated_at"] = now_str()
    path = prompt_abs_path(prompt_rel(p["category"], p["project"], p["title"]))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 关联关系
# ---------------------------------------------------------------------------
def get_out_links(p):
    """出向关联（本片 links 字段）。"""
    return list(p.get("links", []))


def get_in_links(rel):
    """入向关联（扫描其他片指向本片的）。双向可见。"""
    incoming = []
    for _, _, _, r in iter_all_prompts():
        if r == rel:
            continue
        q = load_prompt(r)
        for lk in q.get("links", []):
            if lk.get("target") == rel:
                incoming.append({**lk, "source": r})
    return incoming


def add_link(p, target_rel, note="", overwrite=False):
    """添加关联；overwrite=True 时若已存在则覆盖（更新说明）。"""
    links = p.setdefault("links", [])
    for lk in links:
        if lk["target"] == target_rel:
            if overwrite:
                lk["note"] = note
                return True
            return False
    links.append({"target": target_rel, "relation": "", "note": note})
    return True


def remove_link(p, target_rel):
    p["links"] = [l for l in p.get("links", []) if l["target"] != target_rel]


def _link_fix(old, new):
    """遍历全部提示词片，把 links 中的 old 引用改成 new。"""
    for _, _, _, r in list(iter_all_prompts()):
        q = load_prompt(r)
        changed = False
        for lk in q.get("links", []):
            if lk["target"] == old:
                lk["target"] = new
                changed = True
        if changed:
            save_prompt(q)


def _link_remove(rel_or_prefix):
    """删除全部指向 rel 或前缀 prefix 的关联记录。"""
    for _, _, _, r in list(iter_all_prompts()):
        q = load_prompt(r)
        before = len(q.get("links", []))
        q["links"] = [l for l in q.get("links", [])
                      if l["target"] != rel_or_prefix
                      and not l["target"].startswith(rel_or_prefix)]
        if len(q.get("links", [])) != before:
            save_prompt(q)


# ---------------------------------------------------------------------------
# 项目 / 提示词片操作
# ---------------------------------------------------------------------------
def create_project(category, name):
    d = os.path.join(config.DATA_DIR, category, name)
    if os.path.exists(d):
        return False, "同名项目已存在"
    os.makedirs(d)
    return True, ""


def rename_project(category, old, new):
    old_d, new_d = (os.path.join(config.DATA_DIR, category, old),
                    os.path.join(config.DATA_DIR, category, new))
    if not os.path.isdir(old_d):
        return False, "项目不存在"
    if os.path.exists(new_d):
        return False, "已存在同名项目"
    os.rename(old_d, new_d)
    _link_fix(f"{category}/{old}/", f"{category}/{new}/")
    return True, ""


def delete_project(category, name):
    src = os.path.join(config.DATA_DIR, category, name)
    if not os.path.isdir(src):
        return False
    dst = os.path.join(config.trash_dir(), f"{category}__{name}_{uuid.uuid4().hex[:6]}")
    os.rename(src, dst)
    _link_remove(f"{category}/{name}/")
    return True


def create_prompt(category, project, title):
    rel = prompt_rel(category, project, title)
    if os.path.exists(prompt_abs_path(rel)):
        return False, "同名提示词片已存在"
    save_prompt(new_prompt(category, project, title))
    return True, ""


def rename_prompt(category, project, old, new):
    old_rel = prompt_rel(category, project, old)
    new_rel = prompt_rel(category, project, new)
    if not os.path.exists(prompt_abs_path(old_rel)):
        return False, "提示词片不存在"
    if os.path.exists(prompt_abs_path(new_rel)):
        return False, "已存在同名提示词片"
    os.rename(prompt_abs_path(old_rel), prompt_abs_path(new_rel))
    q = load_prompt(new_rel)
    q["title"] = new
    save_prompt(q)
    _link_fix(old_rel, new_rel)
    return True, ""


def delete_prompt(rel):
    if not os.path.exists(prompt_abs_path(rel)):
        return False
    dst = os.path.join(config.trash_dir(), rel.replace("/", "__") + "_" + uuid.uuid4().hex[:6])
    os.rename(prompt_abs_path(rel), dst)
    _link_remove(rel)
    return True


def copy_prompt(rel, dst_category, dst_project, new_title):
    p = load_prompt(rel)
    p["id"] = uuid.uuid4().hex[:8]
    p["category"], p["project"], p["title"] = dst_category, dst_project, new_title
    p["links"] = []
    p["created_at"] = p["updated_at"] = now_str()
    dst_rel = prompt_rel(dst_category, dst_project, new_title)
    if os.path.exists(prompt_abs_path(dst_rel)):
        return False, "目标位置已存在同名提示词片"
    save_prompt(p)
    return True, ""


# ---------------------------------------------------------------------------
# 数据目录整体迁移（设置里修改存储地址时调用）
# ---------------------------------------------------------------------------
def _move_tree(src, dst):
    """把 src 移到 dst（支持跨磁盘）：先完整复制，成功后删除源。

    跨盘时 os.rename 会失败（WinError 17），shutil.move 的 fallback 会在
    删除源失败时抛异常导致迁移中断 —— 这里先复制保证数据完整，
    删除源失败仅告警不致命（目标已有完整副本）。
    """
    if os.path.isdir(src):
        shutil.copytree(src, dst)
        try:
            shutil.rmtree(src)
        except Exception:
            pass  # 源删除失败不致命：目标已有完整副本
    else:
        shutil.copy2(src, dst)
        try:
            os.remove(src)
        except Exception:
            pass


def migrate_data_dir(new_dir):
    """把全部数据（含回收站）搬运到新目录，成功后更新 config.DATA_DIR 并持久化。"""
    new_dir = os.path.abspath(new_dir)
    if new_dir == os.path.abspath(config.DATA_DIR):
        return False, "目标目录与当前相同"
    if os.path.exists(new_dir) and os.listdir(new_dir):
        return False, "目标目录非空，请选择空目录或不存在的位置"
    os.makedirs(new_dir, exist_ok=True)
    old_dir = config.DATA_DIR
    if os.path.isdir(old_dir):
        for entry in os.listdir(old_dir):
            src = os.path.join(old_dir, entry)
            dst = os.path.join(new_dir, entry)
            if os.path.exists(dst):
                continue
            _move_tree(src, dst)
    config.DATA_DIR = new_dir
    config.save_data_dir(new_dir)   # 持久化数据目录位置（独立配置，重启后恢复）
    ensure_data()
    return True, ""


# ---------------------------------------------------------------------------
# 内容模式：数据 <-> 控件 转换
# ---------------------------------------------------------------------------
def content_to_text(content, fmt):
    """把 content 转成纯文本展示。"""
    if fmt == "chat":
        return "\n".join(f"[{m.get('role', 'user')}] {m.get('content', '')}" for m in (content or []))
    if fmt == "tree":
        lines = []

        def walk(node, depth):
            t = node.get("type") or "节点"
            c = (node.get("content") or "").replace("\n", " ")
            lines.append("  " * depth + f"[{t}] {c}")
            for ch in node.get("children", []):
                walk(ch, depth + 1)

        walk(content or {}, 0)
        return "\n".join(lines)
    return content if isinstance(content, str) else (json.dumps(content, ensure_ascii=False, indent=2) if content else "")


def text_to_content(text, fmt):
    """从纯文本转成对应格式（尽力转换，用于切换格式时的兜底）。"""
    if fmt == "chat":
        msgs = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            role = "user"
            if line.startswith("["):
                end = line.find("]")
                if end > 0:
                    role = line[1:end].strip() or "user"
                    line = line[end + 1:].strip()
            msgs.append({"role": role, "content": line})
        return msgs or [{"role": "user", "content": ""}]
    if fmt == "tree":
        return {"type": "根任务", "content": text, "children": []}
    return text
