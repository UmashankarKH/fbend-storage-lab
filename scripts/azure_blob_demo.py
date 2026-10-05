"""
Azure Blob Storage demo for the storage lab.
Run in Azure Cloud Shell (Bash) from the storage-lab-kit folder:
    pip install --user azure-storage-blob azure-identity
    export STORAGE_ACCOUNT=<your storage account name>
    python scripts/azure_blob_demo.py "how many days do I have to return an item?"
Signs in with your Azure login (no keys in code). You need the
"Storage Blob Data Contributor" role on the storage account.
"""
import csv, io, os, sys
from collections import Counter
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

ACCOUNT = os.environ["STORAGE_ACCOUNT"]
CONTAINER = os.getenv("CONTAINER", "client-docs")
QUESTION = sys.argv[1] if len(sys.argv) > 1 else "how many days do I have to return an item?"

service = BlobServiceClient(f"https://{ACCOUNT}.blob.core.windows.net", credential=DefaultAzureCredential())
container = service.get_container_client(CONTAINER)
if not container.exists():
    container.create_container()
    print(f"Created container {CONTAINER}")

# 1. Upload every file under data/ (keeps the folder names as blob prefixes)
for path in Path("data").rglob("*"):
    if path.is_file():
        name = path.relative_to("data").as_posix()
        with open(path, "rb") as f:
            container.upload_blob(name, f, overwrite=True)
        print(f"uploaded  {name}")

# 2. List what is in the container
print("\nBlobs in container:")
for b in container.list_blobs():
    print(f"  {b.name:40} {b.size:>6} bytes  tier={b.blob_tier}")

# 3. Read the tickets CSV straight from storage (no local file)
text = container.download_blob("tickets/support_tickets.csv").readall().decode("utf-8")
rows = list(csv.DictReader(io.StringIO(text)))
print(f"\n{len(rows)} tickets by category:", dict(Counter(r["category"] for r in rows)))

# 4. The 'R' in RAG: find the policy lines that best match a question
print(f"\nQuestion: {QUESTION}")
words = {w.strip("?.,").lower() for w in QUESTION.split() if len(w) > 3}
hits = []
for b in container.list_blobs(name_starts_with="policies/"):
    for line in container.download_blob(b.name).readall().decode("utf-8").splitlines():
        score = sum(w in line.lower() for w in words)
        if score:
            hits.append((score, b.name, line.strip()))
for score, name, line in sorted(hits, reverse=True)[:3]:
    print(f"  [{name}] {line}")
print("\nAn LLM would now answer using these lines as context.")
