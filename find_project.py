"""Scan all IBM Cloud regions to find where your Watsonx project lives."""
from dotenv import load_dotenv
import os, urllib.request, json, urllib.error

load_dotenv()
apikey = os.getenv("IBM_API_KEY", "").strip()
pid    = os.getenv("IBM_PROJECT_ID", "").strip()

print(f"Searching for project: {pid}")
print()

# ── Get IAM token ──────────────────────────────────────────────────────────────
data  = f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={apikey}".encode()
req   = urllib.request.Request(
    "https://iam.cloud.ibm.com/identity/token",
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
token = json.loads(urllib.request.urlopen(req, timeout=15).read())["access_token"]
print("IAM token: OK")
print()

# ── Check every region ─────────────────────────────────────────────────────────
regions = {
    "us-south": "https://us-south.api.dataplatform.cloud.ibm.com",
    "eu-de":    "https://eu-de.api.dataplatform.cloud.ibm.com",
    "eu-gb":    "https://eu-gb.api.dataplatform.cloud.ibm.com",
    "jp-tok":   "https://jp-tok.api.dataplatform.cloud.ibm.com",
    "au-syd":   "https://au-syd.api.dataplatform.cloud.ibm.com",
    "global":   "https://api.dataplatform.cloud.ibm.com",
}

found = False
for name, base in regions.items():
    try:
        req  = urllib.request.Request(
            f"{base}/v2/projects/{pid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp = urllib.request.urlopen(req, timeout=10)
        body = json.loads(resp.read())
        proj_name = body.get("entity", {}).get("name", "unknown")
        print(f"  FOUND in [{name}]  project name: {proj_name}")
        if name != "global":
            print(f"  --> Set IBM_WATSONX_URL=https://{name}.ml.cloud.ibm.com")
        found = True
    except urllib.error.HTTPError as e:
        print(f"  {name:10s}: HTTP {e.code}")
    except Exception as e:
        print(f"  {name:10s}: {type(e).__name__}")

print()
if not found:
    print("Project NOT found in any region.")
    print()
    print("This means the project was deleted OR the ID was copied incorrectly.")
    print()
    print("ACTION: Go to https://dataplatform.cloud.ibm.com/projects/?context=wx")
    print("        Sign in, open your project, go to Manage -> General")
    print("        Copy the Project ID and update IBM_PROJECT_ID in .env")
