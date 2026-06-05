"""
Sanity Management API Tool for Dify Code Node

在 Dify 的 Code (Python) 节点中运行，负责：
1. 上传生成的图片到 Sanity Assets
2. 创建文章文档 (含引用关系)

环境变量 (在 Dify 中配置):
  - SANITY_PROJECT_ID
  - SANITY_DATASET (默认 "production")
  - SANITY_API_TOKEN (Editor 或更高权限)

使用方式:
  在 Dify Code 节点中粘贴此脚本，输入变量:
    - image_url: 生成的图片 URL
    - article_data: LLM 输出的文章 JSON
    - author_ref: Sanity 作者 _id
"""

import json
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode


# ── Configuration ──────────────────────────────────────────────────
SANITY_PROJECT_ID = "{{env.SANITY_PROJECT_ID}}"
SANITY_DATASET = "{{env.SANITY_DATASET}}" or "production"
SANITY_API_TOKEN = "{{env.SANITY_API_TOKEN}}"

# Sanity API 基础 URL
API_BASE = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v1"
ASSETS_URL = f"{API_BASE}/assets/images/{SANITY_DATASET}"
MUTATE_URL = f"{API_BASE}/data/mutate/{SANITY_DATASET}"


def http_post(url, body=None, content_type="application/json"):
    """发送 POST 请求到 Sanity API"""
    data = json.dumps(body).encode("utf-8") if body else None
    headers = {
        "Authorization": f"Bearer {SANITY_API_TOKEN}",
        "Content-Type": content_type,
    }
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"Sanity API error {e.code}: {error_body}")


def upload_image(image_url):
    """
    上传图片到 Sanity Assets
    返回 asset 的 _id
    """
    # 下载图片
    with urlopen(Request(image_url)) as resp:
        image_data = resp.read()
        content_type = resp.headers.get("Content-Type", "image/png")

    # 上传到 Sanity
    body = {
        "label": f"AI-generated hero image",
        "title": "Article Hero",
    }

    # Sanity assets endpoint expects multipart or POST with body
    from base64 import b64encode

    result = http_post(ASSETS_URL, body)
    # Sanity returns the asset document
    asset_id = result.get("document", {}).get("_id", "")
    if not asset_id:
        raise RuntimeError(f"Image upload failed: {result}")

    return asset_id


def create_article(article_data, image_asset_id):
    """
    创建文章文档
    article_data 包含:
      - title, slug, excerpt, body (HTML string → Portable Text blocks)
      - seoTitle, seoDescription, tags
      - keyTakeaways, faqs
      - category_ref, author_ref
    """
    slug = article_data.get("slug", "")
    if not slug:
        # 从 title 生成 slug
        slug = "-".join(article_data["title"].lower().split())[:80]

    # 将 HTML body 转换为 Sanity Portable Text blocks
    # 简化版: 按段落分割, 每段一个 block
    body_html = article_data.get("body", "")
    body_blocks = html_to_portable_text(body_html)

    mutation = {
        "mutations": [
            {
                "create": {
                    "_type": "article",
                    "title": article_data["title"],
                    "slug": {"_type": "slug", "current": slug},
                    "author": {
                        "_type": "reference",
                        "_ref": article_data.get("author_ref", ""),
                    },
                    "category": {
                        "_type": "reference",
                        "_ref": article_data.get("category_ref", ""),
                    },
                    "heroImage": {
                        "_type": "image",
                        "asset": {"_type": "reference", "_ref": image_asset_id},
                        "alt": article_data.get("image_alt", article_data["title"]),
                    },
                    "excerpt": article_data.get("excerpt", "")[:200],
                    "body": body_blocks,
                    "publishedAt": datetime.now(timezone.utc).isoformat(),
                    "seoTitle": article_data.get("seoTitle", "")[:70],
                    "seoDescription": article_data.get("seoDescription", "")[:160],
                    "tags": article_data.get("tags", []),
                    "keyTakeaways": article_data.get("keyTakeaways", []),
                    "faqs": [
                        {"question": f["question"], "answer": f["answer"]}
                        for f in article_data.get("faqs", [])
                    ],
                }
            }
        ]
    }

    result = http_post(MUTATE_URL, mutation)
    return result


def html_to_portable_text(html):
    """
    将 HTML 转换为 Sanity Portable Text blocks
    简化版实现 — 支持 h2, h3, p, blockquote, ul/li
    """
    import re

    blocks = []
    # 移除 HTML 注释
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    # 提取所有块级元素
    chunk_pattern = re.compile(
        r"<(h[23]|p|blockquote|ul|ol|pre)(?:\s[^>]*)?>(.*?)</\1>",
        re.DOTALL | re.IGNORECASE,
    )
    chunks = chunk_pattern.findall(html)

    for tag, content in chunks:
        tag = tag.lower()
        # 去除内联 HTML 标签
        clean_text = re.sub(r"<[^>]+>", "", content).strip()
        if not clean_text:
            continue

        if tag in ("h2", "h3"):
            level = 2 if tag == "h2" else 3
            blocks.append(
                {
                    "_type": "block",
                    "style": f"h{level}",
                    "children": [
                        {
                            "_type": "span",
                            "text": clean_text,
                        }
                    ],
                }
            )
        elif tag == "blockquote":
            blocks.append(
                {
                    "_type": "block",
                    "style": "blockquote",
                    "children": [
                        {"_type": "span", "text": clean_text}
                    ],
                }
            )
        elif tag == "ul":
            items = re.findall(r"<li>(.*?)</li>", content, re.DOTALL)
            blocks.append(
                {
                    "_type": "block",
                    "style": "normal",
                    "listItem": "bullet",
                    "level": 1,
                    "children": [
                        {
                            "_type": "span",
                            "text": re.sub(r"<[^>]+>", "", item).strip(),
                        }
                        for item in items
                    ],
                }
            )
        elif tag == "p":
            blocks.append(
                {
                    "_type": "block",
                    "style": "normal",
                    "children": [
                        {"_type": "span", "text": clean_text}
                    ],
                }
            )

    return blocks


# ── Main ──────────────────────────────────────────────────────────

def main(image_url: str, article_json_str: str, author_ref: str, category_ref: str):
    """
    Dify Code 节点入口

    参数:
      image_url:     str — 生成的图片 URL
      article_json_str: str — LLM 输出的文章 JSON 字符串
      author_ref:    str — Sanity 作者文档 _id
      category_ref:  str — Sanity 分类文档 _id

    返回:
      dict — {success, article_id, message}
    """
    try:
        article_data = json.loads(article_json_str)
        article_data["author_ref"] = author_ref
        article_data["category_ref"] = category_ref

        # Step 1: 上传图片
        image_asset_id = upload_image(image_url)

        # Step 2: 创建文章文档
        result = create_article(article_data, image_asset_id)

        return {
            "success": True,
            "article_id": result.get("transactionId", ""),
            "image_asset_id": image_asset_id,
            "message": "Article published to Sanity",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# Dify Code 节点自动传入变量
result = main(
    image_url=image_url,
    article_json_str=article_json_str,
    author_ref=author_ref,
    category_ref=category_ref,
)

# 输出为 Dify 可用变量
print(json.dumps(result, ensure_ascii=False))
