"""
针对剩余3个分类生成文章：Movement, Relationships, Sleep
"""
import urllib.request
import json
import re
import os
import ssl
from datetime import datetime, timezone

TOKEN = os.environ["SANITY_API_TOKEN"]
API_KEY = os.environ["DEEPSEEK_API_KEY"]
PID = "o06jwzs8"
DS = "production"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api(url, method="GET", data=None, hdrs=None, to=60):
    if hdrs is None: hdrs = {}
    body = json.dumps(data).encode() if data else None
    if body: hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, method=method)
    for k,v in hdrs.items(): req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=to, context=ctx) as r:
        return json.loads(r.read())

def deepseek(sys, usr, temp=0.8):
    r = api("https://api.deepseek.com/v1/chat/completions", "POST",
        {"model":"deepseek-chat", "messages":[{"role":"system","content":sys},{"role":"user","content":usr}], "temperature":temp, "max_tokens":4096},
        {"Authorization":f"Bearer {API_KEY}"})
    return r["choices"][0]["message"]["content"]

def gen_article(topic, cat_name, cat_id):
    print(f"\n{'='*50}")
    print(f"  {cat_name}: {topic}")
    
    sys = """You are a professional health & wellness content editor for "The Candid Care" website.
Write an original, well-researched article in a warm, conversational, evidence-based tone.
Use short paragraphs, relatable hooks, practical takeaways. Target 400-600 words.
Output ONLY clean Markdown. No meta-commentary."""
    
    txt = deepseek(sys, f"Write a comprehensive article about: {topic}\nCategory: {cat_name}")
    print(f"  ✅ article ({len(txt)} chars)")
    
    # SEO
    seo_txt = deepseek(
        "Generate SEO title (50-60 chars) and meta description (140-160 chars). Output:\nTitle: ...\nDescription: ...",
        txt, temp=0.5)
    
    seo_title = topic
    seo_desc = ""
    for line in seo_txt.strip().split("\n"):
        l = line.strip().lower()
        if l.startswith("title:"): seo_title = line.split(":",1)[1].strip()
        elif l.startswith("description:"): seo_desc = line.split(":",1)[1].strip()
    
    # Slug & excerpt
    slug = re.sub(r'[^a-z0-9]+', '-', seo_title.lower().strip())[:60].strip('-')
    excerpt = txt[:200].strip()
    
    # Publish
    doc = {
        "_type":"article", "_id":slug,
        "title": seo_title,
        "slug":{"_type":"slug","current":slug},
        "body":[{"_type":"block","style":"normal","children":[{"_type":"span","text":txt[:20000]}]}],
        "excerpt":excerpt,
        "author":{"_type":"reference","_ref":"author-default"},
        "category":{"_type":"reference","_ref":cat_id},
        "publishedAt": datetime.now(timezone.utc).isoformat(),
        "seoTitle": seo_title[:70],
        "seoDescription": seo_desc[:160]
    }
    
    r = api(f"https://{PID}.api.sanity.io/v2024-01-01/data/mutate/{DS}", "POST",
        {"mutations":[{"createOrReplace":doc}]},
        {"Authorization":f"Bearer {TOKEN}"})
    
    if "transactionId" in r:
        print(f"  ✅ Published: {slug}")
        return slug
    else:
        print(f"  ❌ Failed")
        return None

# === MAIN ===
targets = [
    ("The Power of Daily Movement: Why Walking Just 30 Minutes Can Transform Your Health", "Movement", "cat-movement"),
    ("Healthy Relationships: Setting Boundaries Without Guilt", "Relationships", "cat-relationships"),
    ("Sleep Science 2026: The Latest Research on How to Actually Sleep Better", "Sleep", "cat-sleep"),
]

slugs = []
for t, cn, ci in targets:
    s = gen_article(t, cn, ci)
    if s: slugs.append(s)

print(f"\n✅ {len(slugs)} articles published!")
for s in slugs: print(f"   /posts/{s}")
