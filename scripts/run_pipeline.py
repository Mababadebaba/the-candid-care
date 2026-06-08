"""
The Candid Care - 内容自动化管道
RSS → DeepSeek AI改写 → SEO元数据 → Sanity发布
直接运行，不需要 Dify
"""
import urllib.request
import xml.etree.ElementTree as ET
import json
import re
import os
import ssl
from datetime import datetime, timezone

# ========== 配置 ==========
SANITY_PROJECT_ID = "o06jwzs8"
SANITY_DATASET = "production"
SANITY_API_TOKEN = os.environ.get("SANITY_API_TOKEN", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
AUTHOR_REF_ID = "author-default"
RSS_URL = "https://rss.nytimes.com/services/xml/rss/nyt/Well.xml"
SITE_URL = "https://the-candid-care.vercel.app"

# SSL context（绕过证书问题）
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

def api_call(url, method="GET", data=None, headers=None, timeout=30):
    """通用 API 调用"""
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


def fetch_rss():
    """步骤1: 抓取 RSS"""
    print("📡 正在抓取 RSS: NYT Well...")
    req = urllib.request.Request(RSS_URL, headers={
        'User-Agent': 'TheCandidCare/1.0',
        'Accept': 'application/rss+xml,application/xml'
    })
    with urllib.request.urlopen(req, timeout=30, context=ssl_context) as resp:
        xml_data = resp.read().decode('utf-8')

    root = ET.fromstring(xml_data)
    items = root.findall('.//item')
    if not items:
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        items = root.findall('.//atom:entry', ns)

    articles = []
    for item in items[:3]:
        title_el = item.find('title')
        link_el = item.find('link')
        desc_el = item.find('description')

        title = title_el.text.strip() if title_el is not None and title_el.text else ''
        link = ''
        if link_el is not None:
            link = link_el.text.strip() if link_el.text else link_el.get('href', '')
        summary = desc_el.text.strip() if desc_el is not None and desc_el.text else ''

        if title:
            articles.append({'title': title, 'link': link, 'summary': summary[:500]})

    print(f"   ✅ 抓取到 {len(articles)} 篇文章")
    return articles


def call_deepseek(system_prompt, user_prompt, temperature=0.7):
    """调用 DeepSeek API"""
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


def rewrite_article(article):
    """步骤2: AI 改写"""
    print(f"   ✍️ 正在改写: {article['title'][:60]}...")
    system_prompt = """You are a professional health & wellness content editor for "The Candid Care" website.

Rewrite the given article into The Candid Care's signature style:
- Warm, inviting, conversational tone
- Evidence-based but accessible language
- Starts with a relatable hook or personal anecdote
- Uses short paragraphs, max 3 sentences each
- Includes practical takeaways for readers
- Target length: 300-500 words

Output ONLY the rewritten article in clean Markdown format. No meta-commentary."""

    user_prompt = f"""**Article Title:** {article['title']}
**Source Link:** {article['link']}
**Original Summary:**
{article['summary']}"""

    result = call_deepseek(system_prompt, user_prompt, temperature=0.7)
    text = result['choices'][0]['message']['content']
    print(f"   ✅ 改写完成 ({len(text)} 字符)")
    return text


def generate_seo(rewritten_text, article_title):
    """步骤3: 生成SEO元数据"""
    print(f"   🔍 正在生成SEO元数据...")
    system_prompt = """You are an SEO/GEO metadata generator for "The Candid Care" wellness blog.

Based on the rewritten article below, generate:
1. **Title:** An SEO-optimized title (50-60 characters). Include primary keyword naturally.
2. **Description:** A compelling meta description (140-160 characters). Include a call-to-action.
3. **Category:** One of these: Mental Health, Mindfulness, Movement, Nutrition, Relationships, Self-Care, Sleep

Output format (strict, each on its own line):
Title: [your SEO title here]
Description: [your meta description here]
Category: [one category from the list]"""

    result = call_deepseek(system_prompt, rewritten_text, temperature=0.5)
    seo_text = result['choices'][0]['message']['content']
    print(f"   ✅ SEO生成完成")

    # 解析 SEO 输出
    seo_title = article_title
    seo_desc = ""
    seo_category = "cat-self-care"

    for line in seo_text.strip().split("\n"):
        line_lower = line.strip().lower()
        if line_lower.startswith("title:"):
            seo_title = line.split(":", 1)[1].strip()
        elif line_lower.startswith("description:"):
            seo_desc = line.split(":", 1)[1].strip()
        elif line_lower.startswith("category:"):
            cat_val = line.split(":", 1)[1].strip().lower().replace(" ", "-")
            valid_cats = ["mental-health", "mindfulness", "movement", "nutrition", "relationships", "self-care", "sleep"]
            for vc in valid_cats:
                if vc in cat_val:
                    seo_category = f"cat-{vc}"
                    break

    return seo_title, seo_desc, seo_category


def publish_to_sanity(title, rewritten_text, seo_title, seo_desc, seo_category):
    """步骤4: 发布到 Sanity"""
    slug = re.sub(r'[^a-z0-9]+', '-', seo_title.lower().strip())[:60].strip('-')

    print(f"   📤 发布到 Sanity (slug: {slug})...")

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
                "text": rewritten_text[:20000]
            }]
        }],
        "excerpt": seo_desc[:200] if seo_desc else rewritten_text[:200],
        "author": {"_type": "reference", "_ref": AUTHOR_REF_ID},
        "category": {"_type": "reference", "_ref": seo_category},
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "seoTitle": seo_title[:70],
        "seoDescription": seo_desc[:160]
    }

    url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2024-01-01/data/mutate/{SANITY_DATASET}"
    headers = {"Authorization": f"Bearer {SANITY_API_TOKEN}"}
    payload = {"mutations": [{"createOrReplace": doc}]}

    result = api_call(url, method="POST", data=payload, headers=headers)

    if 'transactionId' in result:
        print(f"   ✅ 发布成功！URL: {SITE_URL}/posts/{slug}")
        return slug
    else:
        print(f"   ❌ 发布失败: {json.dumps(result)[:200]}")
        return None


def ensure_author_exists():
    """确保 Sanity 中有 author-default"""
    print("👤 检查 author-default 是否存在...")
    query_url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2024-01-01/data/query/{SANITY_DATASET}"
    query = '*[_type == "author" && _id == "author-default"][0]'
    query_url_encoded = f"{query_url}?query={urllib.request.quote(query)}"
    req = urllib.request.Request(query_url_encoded)
    req.add_header('Authorization', f'Bearer {SANITY_API_TOKEN}')
    try:
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
            result = json.loads(resp.read())
            if result.get('result'):
                print("   ✅ author-default 已存在")
                return True
    except Exception:
        pass

    print("   🔧 创建 author-default...")
    author_doc = {
        "_type": "author",
        "_id": AUTHOR_REF_ID,
        "name": "The Candid Care Editorial",
        "bio": "Your trusted source for honest, evidence-based wellness content."
    }
    mutate_url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2024-01-01/data/mutate/{SANITY_DATASET}"
    payload = {"mutations": [{"createOrReplace": author_doc}]}
    headers = {"Authorization": f"Bearer {SANITY_API_TOKEN}"}
    req = urllib.request.Request(mutate_url, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SANITY_API_TOKEN}')
    with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
        result = json.loads(resp.read())
        if 'transactionId' in result:
            print("   ✅ author-default 创建成功")
            return True
        else:
            print(f"   ❌ 创建失败: {result}")
            return False


def ensure_categories_exist():
    """确保 Sanity 中有所有分类"""
    categories = [
        ("cat-mental-health", "Mental Health"),
        ("cat-mindfulness", "Mindfulness"),
        ("cat-movement", "Movement"),
        ("cat-nutrition", "Nutrition"),
        ("cat-relationships", "Relationships"),
        ("cat-self-care", "Self-Care"),
        ("cat-sleep", "Sleep"),
    ]

    print("🏷️  检查分类是否存在...")
    for cat_id, cat_name in categories:
        query = f'*[_type == "category" && _id == "{cat_id}"][0]'
        query_url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2024-01-01/data/query/{SANITY_DATASET}?query={urllib.request.quote(query)}"
        req = urllib.request.Request(query_url)
        req.add_header('Authorization', f'Bearer {SANITY_API_TOKEN}')
        try:
            with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
                result = json.loads(resp.read())
                if result.get('result'):
                    continue
        except Exception:
            pass

        # 不存在，创建
        print(f"   🔧 创建分类: {cat_name}")
        cat_doc = {
            "_type": "category",
            "_id": cat_id,
            "title": cat_name,
            "slug": {"_type": "slug", "current": cat_id.replace("cat-", "")}
        }
        mutate_url = f"https://{SANITY_PROJECT_ID}.api.sanity.io/v2024-01-01/data/mutate/{SANITY_DATASET}"
        payload = {"mutations": [{"createOrReplace": cat_doc}]}
        headers = {"Authorization": f"Bearer {SANITY_API_TOKEN}"}
        req = urllib.request.Request(mutate_url, data=json.dumps(payload).encode('utf-8'), method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {SANITY_API_TOKEN}')
        with urllib.request.urlopen(req, timeout=15, context=ssl_context) as resp:
            result = json.loads(resp.read())
            if 'transactionId' in result:
                print(f"      ✅ {cat_name} 创建成功")

    print("   ✅ 所有分类已确认")


def trigger_vercel_rebuild():
    """触发 Vercel 重新部署"""
    print("🚀 触发 Vercel 重新部署...")
    hook_url = "https://api.vercel.com/v1/integrations/deploy/prj_Ayo7i6gmNQqG1QlkW9q9KL3Bd74c/Um7m5wkvUl"
    try:
        req = urllib.request.Request(hook_url, method='POST')
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
            result = json.loads(resp.read())
            print(f"   ✅ Vercel 部署已触发 (job {result.get('job', {}).get('id', 'N/A')})")
    except Exception as e:
        print(f"   ⚠️  Vercel 触发失败: {e}")


def main():
    print("=" * 60)
    print("  The Candid Care - 内容自动化管道")
    print("=" * 60)
    print()

    if not SANITY_API_TOKEN:
        print("❌ 错误: 请设置环境变量 SANITY_API_TOKEN")
        print("   在终端运行: $env:SANITY_API_TOKEN='your-token'; python run_pipeline.py")
        return

    if not DEEPSEEK_API_KEY:
        print("❌ 错误: 请设置环境变量 DEEPSEEK_API_KEY")
        print("   在终端运行: $env:DEEPSEEK_API_KEY='your-key'; python run_pipeline.py")
        return

    # 0. 确保基础数据存在
    print("📋 步骤0: 检查 Sanity 基础数据...")
    ensure_author_exists()
    ensure_categories_exist()
    print()

    # 1. 抓取 RSS
    print("📋 步骤1: 抓取 RSS")
    articles = fetch_rss()
    if not articles:
        print("   ⚠️  没有抓取到文章，退出。")
        return
    print()

    # 2-4. 逐篇处理
    success_count = 0
    for i, article in enumerate(articles):
        print(f"📋 处理第 {i+1}/{len(articles)} 篇")
        print(f"   标题: {article['title']}")

        # 2. AI 改写
        rewritten = rewrite_article(article)
        if not rewritten:
            print("   ❌ 改写失败，跳过")
            continue

        # 3. 生成 SEO
        seo_title, seo_desc, seo_category = generate_seo(rewritten, article['title'])
        print(f"   📝 SEO标题: {seo_title}")
        print(f"   🏷️  分类: {seo_category}")

        # 4. 发布到 Sanity
        slug = publish_to_sanity(article['title'], rewritten, seo_title, seo_desc, seo_category)
        if slug:
            success_count += 1
        print()

    # 5. 触发 Vercel 重新部署
    print("=" * 60)
    print(f"  ✅ 完成！成功发布 {success_count}/{len(articles)} 篇文章")
    print("=" * 60)
    print()

    if success_count > 0:
        trigger_vercel_rebuild()
        print()
        print("🌐 等待 1-2 分钟后访问:")
        print(f"   {SITE_URL}")
        print("   导航已修复: Self-Care (/self-care), Mindfulness (/mindfulness)")
        print("   ")


if __name__ == "__main__":
    main()
