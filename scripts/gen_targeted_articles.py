"""
针对特定分类生成文章：Nutrition 和 Mindfulness
"""
import urllib.request
import json
import re
import os
import ssl
from datetime import datetime, timezone

SANITY_PROJECT_ID = "o06jwzs8"
SANITY_DATASET = "production"
SANITY_API_TOKEN = os.environ.get("SANITY_API_TOKEN", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
AUTHOR_REF_ID = "author-default"
SITE_URL = "https://the-candid-care.vercel.app"

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def api_call(url, method="GET", data=None, headers=None, timeout=60):
    if headers is None:
        headers = {}
    body = None
    if data:
        body = json.dumps(data).encode('utf-8')
        headers.setdefault('Content-Type', 'application/json')
    req = urllib.request.Request(url, data=body, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as resp:
        return json.loads(resp.read())

def call_deepseek(system_prompt, user_prompt, temperature=0.7):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 4096
    }
    return api_call(url, method="POST", data=payload, headers=headers)

def generate_article(topic, category_name, category_id):
    print(f"\n{'='*60}")
    print(f"📝 生成 {category_name} 文章: {topic}")
    print(f"{'='*60}")

    # Step 1: Write article
    system_prompt = """You are a professional health & wellness content editor for "The Candid Care" website.

Write an original, well-researched article in The Candid Care's signature style:
- Warm, inviting, conversational tone
- Evidence-based but accessible language
- Starts with a relatable hook or personal anecdote
- Uses short paragraphs, max 3 sentences each
- Includes practical takeaways for readers
- Target length: 400-600 words
- Use h2 (##) for section headings

Output ONLY the article in clean Markdown format. No meta-commentary."""

    user_prompt = f"""Write a comprehensive, engaging article about:

**Topic:** {topic}
**Target Category:** {category_name}

Make it feel personal and evidence-based. Include practical tips readers can apply immediately."""

    result = call_deepseek(system_prompt, user_prompt, temperature=0.8)
    article_text = result['choices'][0]['message']['content']
    print(f"   ✅ 文章生成 ({len(article_text)} 字符)")

    # Step 2: Generate SEO metadata
    print(f"   🔍 生成 SEO 元数据...")
    seo_system = """You are an SEO/GEO metadata generator for "The Candid Care" wellness blog.

Based on the article below, generate:
1. Title: SEO-optimized title (50-60 characters), include primary keyword naturally
2. Description: Compelling meta description (140-160 characters) with call-to-action

Output format (strict, each on its own line):
Title: [SEO title]
Description: [meta description]"""

    seo_result = call_deepseek(seo_system, article_text, temperature=0.5)
    seo_text = seo_result['choices'][0]['message']['content']
    
    seo_title = topic
    seo_desc = ""
    for line in seo_text.strip().split("\n"):
        line_lower = line.strip().lower()
        if line_lower.startswith("title:"):
            seo_title = line.split(":", 1)[1].strip()
        elif line_lower.startswith("description:"):
            seo_desc = line.split(":", 1)[1].strip()
    
    print(f"   📝 Title: {seo_title}")
    print(f"   📝 Description: {seo_desc[:80]}...")

    # Step 3: Generate slug and publish
    slug = re.sub(r'[^a-z0-9]+', '-', seo_title.lower().strip())[:60].strip('-')
    
    # Extract excerpt from first paragraph
    excerpt = article_text[:200].strip()
    
    doc = {
        "_type": "article",
        "_id": slug,
        "title": seo_title,
        "slug": {"_type": "slug", "current": slug},
        "body": [{
            "_type": "block",
            "style": "normal",
            "children": [{
                "_type": "span",
                "text": article_text[:20000]
            }]
        }],
        "excerpt": excerpt,
        "author": {"_type": "reference", "_ref": AUTHOR_REF_ID},
        "category": {"_type": "reference", "_ref": category_id},
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "seoTitle": seo_title[:70],
        "seoDescription": seo_desc[:160]
    }

    url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2024-01-01/data/mutate/{SANITY_DATASET}"
    headers = {"Authorization": f"Bearer {SANITY_API_TOKEN}"}
    payload = {"mutations": [{"createOrReplace": doc}]}

    result = api_call(url, method="POST", data=payload, headers=headers)
    
    if 'transactionId' in result:
        print(f"   ✅ 发布成功！{SITE_URL}/posts/{slug}")
        return slug
    else:
        print(f"   ❌ 发布失败: {json.dumps(result)[:200]}")
        return None

def main():
    print("=" * 60)
    print("  针对性文章生成器 - Nutrition + Mindfulness")
    print("=" * 60)

    if not SANITY_API_TOKEN or not DEEPSEEK_API_KEY:
        print("❌ 缺少环境变量")
        return

    articles_to_generate = [
        {
            "topic": "Gut Health and Mental Wellness: The Surprising Link Between What You Eat and How You Feel",
            "category_name": "Nutrition",
            "category_id": "cat-nutrition"
        },
        {
            "topic": "Finding Calm in Chaos: Simple Mindfulness Practices for Busy People",
            "category_name": "Mindfulness",
            "category_id": "cat-mindfulness"
        }
    ]

    slugs = []
    for article in articles_to_generate:
        slug = generate_article(**article)
        if slug:
            slugs.append(slug)

    print(f"\n{'='*60}")
    print(f"✅ 完成！生成了 {len(slugs)} 篇文章")
    for s in slugs:
        print(f"   {SITE_URL}/posts/{s}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
