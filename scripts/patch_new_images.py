"""
Upload hero images and patch Nutrition + Mindfulness articles
"""
import urllib.request
import json
import os
import ssl

SANITY_PID = "o06jwzs8"
DATASET = "production"
TOKEN = os.environ["SANITY_API_TOKEN"]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Image file paths -> article slugs (order matters)
image_map = [
    ("public/images/Healthy_nutrition_concept__col_2026-06-08T01-52-07.png",
     "gut-health-mental-wellness-the-surprising-link-explained",
     "Colorful fresh vegetables and whole grains on rustic table with warm light"),
    ("public/images/Mindfulness_and_meditation__se_2026-06-08T01-52-06.png",
     "simple-mindfulness-practices-for-busy-people-the-candid-care",
     "Serene meditation space with morning light and peace lily plant"),
]

for img_path, slug, alt_text in image_map:
    # Upload image
    print(f"Uploading {img_path}...")
    with open(img_path, "rb") as f:
        img_data = f.read()
    
    url = f"https://{SANITY_PID}.api.sanity.io/v2021-06-07/assets/images/{DATASET}"
    req = urllib.request.Request(url, data=img_data, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "image/png")
    req.add_header("Accept", "application/json")
    
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        result = json.loads(resp.read())
        asset_id = result["document"]["_id"]
        print(f"  Uploaded: {asset_id}")
    
    # Patch article
    print(f"  Patching article {slug}...")
    patch = {
        "mutations": [{
            "patch": {
                "id": slug,
                "set": {
                    "heroImage": {
                        "_type": "image",
                        "asset": {"_type": "reference", "_ref": asset_id},
                        "alt": alt_text
                    }
                }
            }
        }]
    }
    
    murl = f"https://{SANITY_PID}.api.sanity.io/v2024-01-01/data/mutate/{DATASET}"
    req2 = urllib.request.Request(murl, data=json.dumps(patch).encode("utf-8"), method="POST")
    req2.add_header("Authorization", f"Bearer {TOKEN}")
    req2.add_header("Content-Type", "application/json")
    
    with urllib.request.urlopen(req2, timeout=15, context=ctx) as resp:
        r = json.loads(resp.read())
        if "transactionId" in r:
            print(f"  ✅ Patched!")
        else:
            print(f"  ❌ {r}")

print("\nDone! Triggering Vercel deploy...")
hook = "https://api.vercel.com/v1/integrations/deploy/prj_Ayo7i6gmNQqG1QlkW9q9KL3Bd74c/Um7m5wkvUl"
req3 = urllib.request.Request(hook, method="POST")
with urllib.request.urlopen(req3, timeout=10, context=ctx) as resp:
    print(f"  Vercel: {json.loads(resp.read())}")
