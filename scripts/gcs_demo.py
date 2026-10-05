"""
Google Cloud Storage demo for the storage lab.
Run in Google Cloud Shell from the storage-lab-kit folder:
    pip install --user google-cloud-storage
    export BUCKET=<your bucket name>
    python scripts/gcs_demo.py "how many days do I have to return an item?"
Uses your Cloud Shell login (Application Default Credentials). No keys in code.
"""
import csv, io, os, sys
from collections import Counter
from pathlib import Path
from google.cloud import storage

BUCKET = os.environ["BUCKET"]
PREFIX = "client-docs/"
QUESTION = sys.argv[1] if len(sys.argv) > 1 else "how many days do I have to return an item?"

client = storage.Client()
bucket = client.bucket(BUCKET)

# 1. Upload every file under data/
for path in Path("data").rglob("*"):
    if path.is_file():
        name = PREFIX + path.relative_to("data").as_posix()
        bucket.blob(name).upload_from_filename(str(path))
        print(f"uploaded  {name}")

# 2. List objects
print("\nObjects in bucket:")
for b in client.list_blobs(BUCKET, prefix=PREFIX):
    print(f"  {b.name:50} {b.size:>6} bytes  class={b.storage_class}")

# 3. Read the tickets CSV straight from storage
text = bucket.blob(PREFIX + "tickets/support_tickets.csv").download_as_text()
rows = list(csv.DictReader(io.StringIO(text)))
print(f"\n{len(rows)} tickets by category:", dict(Counter(r["category"] for r in rows)))

# 4. The 'R' in RAG: find the policy lines that best match a question
print(f"\nQuestion: {QUESTION}")
words = {w.strip("?.,").lower() for w in QUESTION.split() if len(w) > 3}
hits = []
for b in client.list_blobs(BUCKET, prefix=PREFIX + "policies/"):
    for line in b.download_as_text().splitlines():
        score = sum(w in line.lower() for w in words)
        if score:
            hits.append((score, b.name, line.strip()))
for score, name, line in sorted(hits, reverse=True)[:3]:
    print(f"  [{name}] {line}")
print("\nAn LLM would now answer using these lines as context.")
