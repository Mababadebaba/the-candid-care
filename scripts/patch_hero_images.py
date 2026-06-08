"""Patch articles with heroImage references"""
import urllib.request, json, ssl, os

token = os.environ["SANITY_API_TOKEN"]
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Step 1: Get articles
query = '*[_type == "article"] | order(publishedAt desc)[0...3]{_id, title}'
qurl = ("https://o06jwzs8.api.sanity.io/v2024-01-01/data/query/production?query="
        + urllib.request.quote(query))
req = urllib.request.Request(qurl)
req.add_header("Authorization", "Bearer " + token)
with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
    articles = json.loads(resp.read())["result"]

print("Found", len(articles), "articles:")
for a in articles:
    print(f"  {a['_id']} - {a['title'][:60]}")

# Step 2: Asset IDs
assets = [
    "image-45f4725a8ce11b9f4ca267d2863cb5383f75b1a6-1024x1024-png",
    "image-7ed647d5f2e4dba6206da1c77773140622d1afd6-1024x1024-png",
    "image-efec3dd5369e8578bb149a531e006bca143a932e-1024x1024-png",
]
alts = [
    "Serene wellness lifestyle photography with natural light and plants",
    "Calming self-care scene with candles, essential oils and warm lighting",
    "Elegant minimal healthcare concept with fresh plants and notebook",
]

# Step 3: Patch
murl = "https://o06jwzs8.api.sanity.io/v2024-01-01/data/mutate/production"
for i, article in enumerate(articles):
    patch = {
        "mutations": [{
            "patch": {
                "id": article["_id"],
                "set": {
                    "heroImage": {
                        "_type": "image",
                        "asset": {"_type": "reference", "_ref": assets[i]},
                        "alt": alts[i],
                    }
                }
            }
        }]
    }
    body = json.dumps(patch).encode("utf-8")
    req = urllib.request.Request(murl, data=body, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        result = json.loads(resp.read())
        if "transactionId" in result:
            print(f"  ✅ {article['title'][:50]}")
        else:
            print(f"  ❌ {result}")

print("\nDone! 3 articles patched with heroImage.")
