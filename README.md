# reading-paper-arxiv

> 一条命令，把 arXiv 论文变成图文并茂的中文阅读笔记。

这是一个 [Claude Code](https://claude.ai/claude-code) skill，输入 arXiv 链接，自动完成：从 arXiv API 拉取元数据、从源码包提取原始高清图片，到生成结构完整的中文 Markdown 笔记——全程无需手动操作。

---

## 效果预览

```
/reading-paper-arxiv https://arxiv.org/abs/2603.05344
```

输出：

```
当前目录/
└── Building_Effective_AI_Coding_Agents_for_the_Terminal_Scaffol/
    ├── Building_Effective_AI_Coding_Agents_for_the_Terminal.md   ← 详细中文笔记
    └── images/
        ├── fig1.png     ← 从 arXiv 源码包提取的原始矢量图
        ├── fig2.png
        └── ...（按论文顺序编号，通常 10～40+ 张）
```

生成笔记包含：研究背景与问题、核心贡献、方法详解（图文对照）、实验结果、深度思考、关键概念 WikiLink、参考文献梳理……

---

## 安装

### 前提条件

- [Claude Code](https://claude.ai/claude-code) CLI 已安装并登录
- Python 3.8+（仅用标准库，无需额外依赖）

### 安装步骤

将 `reading-paper-arxiv` 文件夹复制到 Claude Code 的 skills 目录：

**macOS / Linux**
```bash
cp -r reading-paper-arxiv ~/.claude/skills/
```

**Windows**
```powershell
Copy-Item -Recurse reading-paper-arxiv "$env:USERPROFILE\.claude\skills\"
```

重启 Claude Code 后，skill 自动加载，输入 `/reading-paper-arxiv` 即可触发。

---

## 使用方式

在 Claude Code 中，直接输入：

```
/reading-paper-arxiv <arXiv 链接或 ID>
```

支持以下输入格式：

```
/reading-paper-arxiv https://arxiv.org/abs/2506.12345
/reading-paper-arxiv https://arxiv.org/pdf/2506.12345
/reading-paper-arxiv 2506.12345
```

笔记保存在**当前工作目录**，切换到你的论文库目录再调用，笔记就直接落在那里。

---

## 工作原理

```
输入 arXiv 链接
       │
       ▼
① 解析 arXiv ID
       │
       ▼
② 调用 arXiv API 获取元数据
   （标题、作者、摘要、发布日期、分类……）
       │
       ▼
③ 下载 arXiv 源码包 (.tar.gz)
   提取所有论文图片 → fig1.png, fig2.png ...
   （优先原始矢量图/高清图，无源码包时跳过）
       │
       ▼
④ Claude 阅读全文 + 逐图解读
       │
       ▼
⑤ 生成结构化中文 Markdown 笔记
   图文对照，WikiLink 标注关键概念
```

核心脚本 `scripts/fetch_paper.py` 纯 Python 标准库实现，跨平台，支持 SSL 证书宽松模式（解决部分企业网络限制）。

---

## 笔记结构

每篇论文笔记包含以下章节：

| 章节 | 内容 |
|------|------|
| 基本信息 | 作者、机构、日期、分类、arXiv 链接 |
| 研究背景与问题 | 问题来源、现有方案的不足 |
| 核心贡献 | 论文的主要创新点列表 |
| 方法详解 | 架构图解读、关键设计逐一分析，图文对照 |
| 实验结果 | 数据集、基线对比、主要指标 |
| 深度思考 | 创新点分析、局限性、与相关工作对比表 |
| 关键概念 | `[[WikiLink]]` 格式，适配 Obsidian 知识图谱 |
| 我的阅读笔记 | 个人理解、启发、待研究的问题 |
| 参考文献 | Related Work 中重要论文梳理 |

---

## 技术说明

- **图片来源优先级**：arXiv 源码包 (`.tar.gz`) > 无法提取时跳过
- **图片命名**：按论文中出现顺序统一命名为 `fig1.png`, `fig2.png` ...（PDF 格式图保留为 `.pdf`）
- **文件夹名**：论文英文标题，空格转下划线，去除特殊字符，最长 60 字符
- **笔记语言**：中文，专有名词（模型名、方法名）保留英文
- **WikiLink**：所有核心概念、引用论文用 `[[]]` 包裹，可直接导入 Obsidian

---

## License

MIT © 2026 Zihang Ma
