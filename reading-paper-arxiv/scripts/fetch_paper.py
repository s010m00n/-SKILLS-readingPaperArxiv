#!/usr/bin/env python3
"""
fetch_paper.py - 从 arXiv 获取论文元数据并提取图片

用法：
  # 只获取元数据
  python fetch_paper.py --id 2506.12345 --output paper_meta.json

  # 获取元数据 + 提取图片
  python fetch_paper.py --id 2506.12345 --extract-images --images-dir ./images
"""

import argparse
import json
import os
import re
import ssl
import sys
import tarfile
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# SSL context that works on Windows
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def parse_arxiv_id(raw: str) -> str:
    """从 URL 或原始 ID 中提取 arXiv ID"""
    raw = raw.strip().rstrip('/')
    # 匹配 URL 格式
    m = re.search(r'arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)', raw)
    if m:
        return m.group(1)
    # 匹配纯 ID 格式
    m = re.match(r'^([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)$', raw)
    if m:
        return m.group(1)
    raise ValueError(f"无法识别 arXiv ID: {raw}")


def _urlopen(url: str, timeout: int = 60) -> bytes:
    """统一的 HTTP 请求，带重试"""
    req = urllib.request.Request(url, headers={'User-Agent': 'reading-paper-arxiv/1.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as resp:
                return resp.read()
        except Exception as e:
            if attempt == 2:
                raise
            print(f"[fetch] 重试 ({attempt+1}/3): {e}", file=sys.stderr)
    raise RuntimeError("请求失败")


def fetch_metadata(arxiv_id: str) -> dict:
    """调用 arXiv API 获取论文元数据"""
    base_id = re.sub(r'v\d+$', '', arxiv_id)

    # 直接用 HTTPS，避免 http→https 重定向超时
    url = f"https://arxiv.org/api/query?id_list={base_id}&max_results=1"
    print(f"[fetch] arXiv API: {url}", file=sys.stderr)

    content = _urlopen(url, timeout=60).decode('utf-8')
    return _parse_arxiv_xml(content, arxiv_id, base_id)


def _parse_arxiv_xml(content: str, arxiv_id: str, base_id: str) -> dict:

    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    root = ET.fromstring(content)
    entry = root.find('atom:entry', ns)

    if entry is None:
        raise ValueError(f"未找到论文: {arxiv_id}")

    # 提取作者
    authors = []
    for author in entry.findall('atom:author', ns):
        name = author.find('atom:name', ns)
        if name is not None:
            authors.append(name.text.strip())

    # 提取机构（affiliation）
    affiliations = []
    for author in entry.findall('atom:author', ns):
        aff = author.find('arxiv:affiliation', ns)
        if aff is not None and aff.text:
            affiliations.append(aff.text.strip())

    # 提取分类
    categories = []
    for cat in entry.findall('atom:category', ns):
        term = cat.get('term', '')
        if term:
            categories.append(term)

    # 提取链接
    pdf_url = ''
    arxiv_url = ''
    for link in entry.findall('atom:link', ns):
        rel = link.get('rel', '')
        href = link.get('href', '')
        title = link.get('title', '')
        if title == 'pdf':
            pdf_url = href
        elif rel == 'alternate':
            arxiv_url = href

    title_el = entry.find('atom:title', ns)
    abstract_el = entry.find('atom:summary', ns)
    published_el = entry.find('atom:published', ns)

    title = title_el.text.strip().replace('\n', ' ') if title_el is not None else ''
    abstract = abstract_el.text.strip().replace('\n', ' ') if abstract_el is not None else ''
    published = published_el.text.strip()[:10] if published_el is not None else ''

    # 源码包 URL
    source_url = f"https://arxiv.org/src/{base_id}"

    return {
        'id': arxiv_id,
        'base_id': base_id,
        'title': title,
        'authors': authors,
        'affiliations': list(set(affiliations)),
        'abstract': abstract,
        'published': published,
        'categories': categories,
        'pdf_url': pdf_url or f"https://arxiv.org/pdf/{base_id}",
        'arxiv_url': arxiv_url or f"https://arxiv.org/abs/{base_id}",
        'source_url': source_url,
    }


def sanitize_filename(name: str, max_len: int = 60) -> str:
    """将标题转换为合法文件名"""
    # 去掉特殊字符，空格换下划线
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    name = re.sub(r'_+', '_', name)
    return name[:max_len].rstrip('_')


def extract_images_from_source(base_id: str, images_dir: str) -> list:
    """从 arXiv 源码包提取图片"""
    images_dir = Path(images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    source_url = f"https://arxiv.org/src/{base_id}"
    print(f"[images] 下载源码包: {source_url}", file=sys.stderr)

    tar_path = images_dir / "_source.tar.gz"

    try:
        req = urllib.request.Request(
            source_url,
            headers={'User-Agent': 'reading-paper-arxiv/1.0'}
        )
        with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
            with open(tar_path, 'wb') as f:
                f.write(resp.read())
    except urllib.error.HTTPError as e:
        print(f"[images] 源码包下载失败 ({e.code})，跳过图片提取", file=sys.stderr)
        return []

    # 图片扩展名
    IMG_EXTS = {'.png', '.jpg', '.jpeg', '.pdf', '.eps', '.svg'}
    # 排除 logo、icon 等非论文图片
    EXCLUDE_PATTERNS = ['logo', 'icon', 'badge', 'orcid', 'arxiv_logo']

    extracted = []

    try:
        with tarfile.open(tar_path, 'r:gz') as tar:
            members = tar.getmembers()

            # 找出所有图片文件
            img_members = []
            for m in members:
                p = Path(m.name)
                if p.suffix.lower() in IMG_EXTS:
                    name_lower = p.stem.lower()
                    if not any(pat in name_lower for pat in EXCLUDE_PATTERNS):
                        img_members.append(m)

            # 按文件名排序
            img_members.sort(key=lambda m: Path(m.name).name.lower())

            for i, member in enumerate(img_members, 1):
                src_path = Path(member.name)
                # 统一命名为 fig1.png, fig2.png ...
                ext = src_path.suffix.lower()
                if ext == '.pdf':
                    ext = '.pdf'  # 保留 PDF 格式的图
                elif ext in {'.eps', '.svg'}:
                    ext = '.png'  # 后续可转换，先保存原格式

                out_name = f"fig{i}{src_path.suffix.lower()}"
                out_path = images_dir / out_name

                try:
                    f = tar.extractfile(member)
                    if f:
                        with open(out_path, 'wb') as out_f:
                            out_f.write(f.read())
                        extracted.append(str(out_path))
                        print(f"[images] 提取: {member.name} → {out_name}", file=sys.stderr)
                except Exception as e:
                    print(f"[images] 跳过 {member.name}: {e}", file=sys.stderr)

    except tarfile.TarError as e:
        print(f"[images] 解压失败: {e}", file=sys.stderr)
    finally:
        # 清理临时文件
        if tar_path.exists():
            tar_path.unlink()

    return extracted


def main():
    parser = argparse.ArgumentParser(description='获取 arXiv 论文元数据并提取图片')
    parser.add_argument('--id', required=True, help='arXiv ID 或 URL')
    parser.add_argument('--output', help='元数据输出 JSON 文件路径')
    parser.add_argument('--extract-images', action='store_true', help='是否提取图片')
    parser.add_argument('--images-dir', default='./images', help='图片保存目录')
    args = parser.parse_args()

    # 解析 ID
    try:
        arxiv_id = parse_arxiv_id(args.id)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    # 获取元数据
    print(f"[fetch] arXiv ID: {arxiv_id}", file=sys.stderr)
    meta = fetch_metadata(arxiv_id)
    meta['folder_name'] = sanitize_filename(meta['title'])

    # 提取图片
    if args.extract_images:
        images = extract_images_from_source(meta['base_id'], args.images_dir)
        meta['images'] = images
        meta['images_dir'] = args.images_dir
        print(f"[images] 共提取 {len(images)} 张图片", file=sys.stderr)

    # 输出结果
    result = json.dumps(meta, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"[fetch] 元数据已保存到: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == '__main__':
    main()
