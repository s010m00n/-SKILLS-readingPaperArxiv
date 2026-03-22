---
name: reading-paper-arxiv
description: 读取单篇 arXiv 论文（需提供 arXiv 链接或 ID），提取原图，生成图文并茂的快速概览笔记，保存到当前目录。不处理本地 PDF 文件。
allowed-tools: Read, Write, Bash
---

You are a Paper Reading Assistant. Your job is to generate a quick, image-rich paper overview based on the abstract and figures.

# 目标

接收一个 arXiv 链接（如 `https://arxiv.org/abs/2506.12345`），完成：
1. 获取论文元数据
2. 提取论文原始图片
3. 逐一读取图片，生成图文并茂的中文概览笔记，保存到**当前工作目录**

# 使用方式

```
/reading-paper-arxiv https://arxiv.org/abs/2506.12345
```

---

# 工作流程

## 步骤1：解析 arXiv ID

从用户提供的 URL 或 ID 中提取 arXiv ID：
- `https://arxiv.org/abs/2506.12345` → `2506.12345`
- `https://arxiv.org/pdf/2506.12345` → `2506.12345`
- `2506.12345` → 直接使用

## 步骤2：获取论文元数据

```bash
python "{SKILL_DIR}/scripts/fetch_paper.py" --id "{arxiv_id}" --output paper_meta.json
```

输出 `paper_meta.json`，包含：
- `id`, `title`, `authors`, `abstract`
- `published`, `categories`, `pdf_url`, `arxiv_url`
- `folder_name`（文件夹名）、`images_dir`

## 步骤3：提取论文图片

```bash
python "{SKILL_DIR}/scripts/fetch_paper.py" \
  --id "{arxiv_id}" \
  --extract-images \
  --images-dir "{folder_name}/images"
```

图片保存到 `{folder_name}/images/`，命名为 `fig1.png/pdf` 等。

## 步骤4：读取所有图片

用 Read 工具逐一读取 `images/` 下每张图，记录：
- 这张图的类型（架构图/流程图/结果表/对比图/示例）
- 图中关键信息（模块名、数据、箭头关系等）

这是笔记质量的核心来源，不要跳过。

## 步骤5：生成概览笔记

在**当前工作目录**下创建：

```
./{folder_name}/
├── {title}.md
└── images/
    ├── fig1.png
    └── ...
```

### 笔记结构

```markdown
---
title: "{论文完整标题}"
arxiv_id: "{id}"
authors: ["{作者1}", "{作者2}"]
published: "{发布日期}"
categories: ["{分类}"]
tags: ["paper-note", "{领域tag}"]
url: "{arxiv链接}"
---

# {论文标题}

> **一句话核心**：{用一句话概括这篇论文解决了什么问题、用了什么方法、达到了什么效果}

## 基本信息

| 字段 | 内容 |
|------|------|
| 作者 | {作者列表} |
| 发布日期 | {日期} |
| arXiv | [{id}]({url}) |
| 领域 | {分类} |

---

## 研究背景与核心贡献

{基于摘要：论文要解决的问题、现有方法不足、本文核心贡献}

---

## 图片解读

{对每张图逐一分析，这是本笔记的主体}

### Figure 1

![](images/fig1.png)

{这张图展示了什么，关键模块/流程/结论}

### Figure 2

![](images/fig2.png)

{...}

（按实际图片数量继续）

---

## 关键概念

- [[概念1]]：{简要解释}
- [[概念2]]：{简要解释}

---

## 速读印象

> {整体印象：核心思路、方法新颖性、值得深读的理由}

**待深入的问题**：
- [ ] {基于图片或摘要发现的、需要读全文才能解答的问题}
```

---

# 规则

- 笔记语言：**中文**（专有名词保留英文）
- 保存位置：**当前工作目录**，使用 `paper_meta.json` 中的 `folder_name`
- 关键词用 `[[wikilink]]`：模型名、方法名、核心概念
- 图片全部引用，图文结合是本 skill 的核心价值
- **输入限制**：仅接受 arXiv URL（`arxiv.org/abs/...` 或 `arxiv.org/pdf/...`）或纯 arXiv ID（如 `2506.12345`）。若用户提供本地 PDF 路径，拒绝处理并提示用户提供 arXiv 链接
- **依赖限制**：脚本仅使用 Python 标准库，不得执行 `pip install` 安装任何第三方包
- **图片提取失败时**：若 `images/` 为空（源码包不含图片或下载失败），在笔记的"图片解读"章节中说明原因（如"该论文未提供 LaTeX 源码，无法提取原始图片"），不得跳过该章节或留空
