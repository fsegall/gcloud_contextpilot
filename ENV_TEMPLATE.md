# Environment Variables Template

Copy this to `.env` in the project root or `back-end/.env`:

```bash
# Google Gemini API Key (required)
# Get from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your-gemini-api-key-here

# Optional (for production)
GCP_PROJECT_ID=your-gcp-project-id
GITHUB_TOKEN=your-github-token
FIRESTORE_ENABLED=false
USE_PUBSUB=false
# For production on GCP and Cloud Run:
# FIRESTORE_ENABLED=true   # Uses Firestore (persistent, scalable)
# USE_PUBSUB=true          # Uses Pub/Sub (async, multi-agent)
```



## Quick Start

**Docker Compose:**
```bash
echo "GOOGLE_API_KEY=your-key" > .env
docker-compose up
```

**Local Python:**
```bash
cd back-end
cp ENV_TEMPLATE.md .env  # Edit with your key
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.server:app --reload
```
