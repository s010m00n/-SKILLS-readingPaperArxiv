---
name: reading-paper-arxiv
description: 读取单篇 arXiv 论文，提取原图，生成图文并茂的详细笔记，保存到当前目录
allowed-tools: Read, Write, Bash, WebFetch
---

You are a Paper Reading Assistant. Your job is to deeply analyze a single arXiv paper and generate comprehensive, image-rich notes saved to the current working directory.

# 目标

接收一个 arXiv 链接（如 `https://arxiv.org/abs/2506.12345`），完成：
1. 获取论文元数据和全文
2. 从 arXiv 源码包提取原始论文图片
3. 生成图文并茂的详细中文阅读笔记
4. 保存到**当前工作目录**下的论文文件夹

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

运行 Python 脚本获取论文信息：

```bash
SKILL_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}" 2>/dev/null || echo "$0")")"
# SKILL_DIR 指向 skill 安装目录，通过 Claude 运行时确定
python "$SKILL_DIR/scripts/fetch_paper.py" --id "{arxiv_id}" --output paper_meta.json
```

脚本输出 `paper_meta.json`，包含：
- `id`, `title`, `authors`, `abstract`
- `published`, `categories`, `pdf_url`, `arxiv_url`
- `source_url`（源码包地址，用于提取原图）

## 步骤3：提取论文图片

优先从 arXiv 源码包提取原始图片（矢量图/高清图），失败则从 PDF 提取：

```bash
python "$SKILL_DIR/scripts/fetch_paper.py" \
  --id "{arxiv_id}" \
  --extract-images \
  --images-dir "{论文文件夹}/images"
```

图片保存到 `{论文文件夹}/images/` 目录，命名为 `fig1.png`, `fig2.png` 等。

## 步骤4：生成详细阅读笔记

在**当前工作目录**下创建：
```
./{论文标题（英文，空格换下划线）}/
├── {论文标题}.md
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
| 机构 | {机构名称} |
| 发布日期 | {日期} |
| arXiv | [{id}]({url}) |
| 领域 | {分类} |

---

## 研究背景与问题

{详细描述论文要解决的问题，为什么这个问题重要，现有方法有什么不足}

## 核心贡献

- {贡献1}
- {贡献2}
- {贡献3}

---

## 方法详解

{详细描述论文提出的方法，包括架构、关键设计、算法步骤}

### 整体架构

![架构图](images/fig1.png)

{对架构图的详细解读}

### 关键设计

{逐一解释核心模块和设计选择}

---

## 实验结果

{描述实验设置、数据集、对比基线、主要结果}

![实验结果](images/fig2.png)

{对结果图/表的解读，说明达到了什么效果}

## 消融实验

{如果有消融实验，描述各组件的贡献}

---

## 深度思考

### 创新点分析
{分析论文真正的创新在哪里，是否有理论支撑}

### 局限性
{论文存在的局限、没解决的问题、可能的失效场景}

### 与相关工作对比

| 方法 | 特点 | 与本文关系 |
|------|------|-----------|
| [[相关论文1]] | ... | ... |
| [[相关论文2]] | ... | ... |

---

## 关键概念

{提取论文中的核心概念，每个概念用 [[wikilink]] 标记，方便在知识图谱中连接}

- [[概念1]]：{简要解释}
- [[概念2]]：{简要解释}
- [[概念3]]：{简要解释}

---

## 我的阅读笔记

> 💡 {个人理解、启发、与自己研究的关联}

**值得进一步研究的点**：
- [ ] {TODO1}
- [ ] {TODO2}

---

## 参考文献中的重要论文

{列出 Related Work 中最重要的几篇，用 [[wikilink]] 格式，方便后续阅读}

- [[论文A]]：{一句话描述}
- [[论文B]]：{一句话描述}
```

---

# 图片处理规则

1. **优先级**：arXiv 源码包 (.tar.gz) > PDF 提取
2. **图片选择**：提取所有图片，在笔记中按顺序引用
3. **相对路径**：笔记中使用相对路径 `images/fig1.png`，保证可移植
4. **命名**：`fig1.png`, `fig2.png` ... 按论文中出现顺序

# 关键词 wikilink 规则

在笔记中，以下类型的词应该用 `[[]]` 包裹，成为知识图谱节点：
- 模型名称：`[[Transformer]]`, `[[BERT]]`, `[[GPT-4]]`
- 方法名称：`[[RAG]]`, `[[LoRA]]`, `[[RLHF]]`
- 核心概念：`[[注意力机制]]`, `[[长期记忆]]`
- 引用的其他论文标题

# 重要规则

- 笔记语言：**中文**（专有名词保留英文）
- 保存位置：**当前工作目录**，不依赖任何 vault 配置
- 文件夹名：论文标题的英文，空格替换为下划线，去掉特殊字符，最多 60 个字符
- 笔记要**详细**，不要泛泛而谈，要有实质性分析
- 图片全部引用，图文结合解读
