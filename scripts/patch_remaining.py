"""Upload 3 images + patch Movement, Relationships, Sleep articles"""
import urllib.request, json, os, ssl

T = os.environ["SANITY_API_TOKEN"]
PID = "o06jwzs8"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

maps = [
    ("public/images/Movement_and_exercise_wellness_2026-06-08T04-59-55.png",
     "the-power-of-daily-movement-why-walking-just-30-minutes-can",
     "Morning walk in nature with golden sunrise through forest trees"),
    ("public/images/Healthy_relationships_and_conn_2026-06-08T05-00-22.png",
     "healthy-relationships-setting-boundaries-without-guilt",
     "Two warm ceramic teacups on wooden table with fresh flowers"),
    ("public/images/Sleep_wellness__cozy_bedroom_a_2026-06-08T05-00-49.png",
     "sleep-science-2026-the-latest-research-on-how-to-actually-sl",
     "Cozy bedroom at dawn with linen bedding and sleep journal"),
]

for img_path, slug, alt in maps:
    # Upload
    print(f"Uploading {img_path.split('/')[-1][:40]}...")
    with open(img_path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(
        f"https://{PID}.api.sanity.io/v2021-06-07/assets/images/production",
        data=data, method="POST")
    req.add_header("Authorization", f"Bearer {T}")
    req.add_header("Content-Type", "image/png")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        aid = json.loads(r.read())["document"]["_id"]
        print(f"  uploaded: {aid}")
    
    # Patch
    patch = {"mutations":[{"patch":{"id":slug, "set":{
        "heroImage":{"_type":"image","asset":{"_type":"reference","_ref":aid},"alt":alt}
    }}}]}
    req2 = urllib.request.Request(
        f"https://{PID}.api.sanity.io/v2024-01-01/data/mutate/production",
        data=json.dumps(patch).encode(), method="POST")
    req2.add_header("Authorization", f"Bearer {T}")
    req2.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req2, timeout=15, context=ctx) as r:
        res = json.loads(r.read())
        print(f"  patched: {'✅' if 'transactionId' in res else '❌'}")

print("\nAll done!")
