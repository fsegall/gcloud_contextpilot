# ContextPilot - Terraform Infrastructure

**Infrastructure as Code for Google Cloud Platform**

---

## 🎯 What This Does

This Terraform configuration deploys the complete ContextPilot infrastructure on Google Cloud:

- ✅ **Cloud Run** - Backend API service
- ✅ **Pub/Sub** - Event bus (11 topics + 5 subscriptions)
- ✅ **Firestore** - NoSQL database
- ✅ **Secret Manager** - Secure API key storage
- ✅ **IAM Permissions** - Service account access

**Deploy everything with one command:** `terraform apply`

---

## 📋 Prerequisites

### 1. Install Terraform
```bash
# Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# Verify
terraform --version
```

### 2. Google Cloud Setup
```bash
# Authenticate
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project contextpilot-hack-4044
```

### 3. Build and Push Docker Image
```bash
cd ../back-end
docker build -t gcr.io/contextpilot-hack-4044/contextpilot-backend:latest .
docker push gcr.io/contextpilot-hack-4044/contextpilot-backend:latest
```

---

## 🚀 Quick Start

### Deploy Everything
```bash
cd terraform

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy!
terraform apply
```

**That's it!** ✨ Your infrastructure is deployed!

---

## 📊 What Gets Created

### Enabled APIs (6)
- Cloud Run API
- Container Registry API
- Cloud Build API
- Pub/Sub API
- Firestore API
- Secret Manager API

### Pub/Sub Topics (11)
- `git-events`
- `proposal-events`
- `context-events`
- `spec-events`
- `strategy-events`
- `milestone-events`
- `coach-events`
- `retrospective-events`
- `artifact-events`
- `reward-events`
- `dead-letter-queue`

### Pub/Sub Subscriptions (5)
- `spec-agent-sub` → spec-events
- `git-agent-sub` → git-events
- `strategy-agent-sub` → strategy-events
- `coach-agent-sub` → coach-events
- `retrospective-agent-sub` → retrospective-events

### Cloud Run Service
- **Name:** contextpilot-backend
- **Memory:** 512Mi
- **CPU:** 1
- **Max Instances:** 10
- **Min Instances:** 0
- **Public Access:** Enabled

### Firestore Database
- **Type:** Native mode
- **Location:** us-central1

### Secret Manager
- **GOOGLE_API_KEY:** Gemini API key (you need to add the value)

---

## 🔧 Configuration

### Variables

Edit `terraform.tfvars` to customize:

```hcl
project_id    = "your-project-id"
region        = "us-central1"
backend_image = "gcr.io/your-project-id/contextpilot-backend:latest"
environment   = "production"
```

Or pass via command line:
```bash
terraform apply -var="project_id=my-project"
```

---

## 🔐 Adding Secrets

After deployment, add your API keys:

```bash
# Add Gemini API key
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-

# Verify
gcloud secrets versions access latest --secret="GOOGLE_API_KEY"
```

---

## 📈 Terraform State

### Local State (Default)
State is stored in `terraform.tfstate` locally.

### Remote State (Recommended for Production)
Uncomment in `main.tf`:
```hcl
backend "gcs" {
  bucket = "contextpilot-terraform-state"
  prefix = "terraform/state"
}
```

Create the bucket:
```bash
gsutil mb gs://contextpilot-terraform-state
gsutil versioning set on gs://contextpilot-terraform-state
```

---

## 🧪 Testing Deployment

After `terraform apply`:

```bash
# Get Cloud Run URL
CLOUD_RUN_URL=$(terraform output -raw cloud_run_url)

# Test health endpoint
curl $CLOUD_RUN_URL/health

# Test agents
curl $CLOUD_RUN_URL/agents/status

# View all outputs
terraform output
```

---

## 🔄 Updating Infrastructure

### Update Backend Image
```bash
# Build and push new image
cd ../back-end
docker build -t gcr.io/contextpilot-hack-4044/contextpilot-backend:v2 .
docker push gcr.io/contextpilot-hack-4044/contextpilot-backend:v2

# Update terraform
cd ../terraform
terraform apply -var="backend_image=gcr.io/contextpilot-hack-4044/contextpilot-backend:v2"
```

### Add New Pub/Sub Topic
Edit `main.tf`:
```hcl
resource "google_pubsub_topic" "event_topics" {
  for_each = toset([
    # ... existing topics
    "new-topic-name",  # Add here
  ])
  # ...
}
```

Then:
```bash
terraform apply
```

---

## 🗑️ Destroying Infrastructure

**⚠️ WARNING: This will delete everything!**

```bash
terraform destroy
```

To destroy specific resources:
```bash
# Destroy only Cloud Run
terraform destroy -target=google_cloud_run_service.backend

# Destroy only Pub/Sub topics
terraform destroy -target=google_pubsub_topic.event_topics
```

---

## 📊 Outputs

After deployment, Terraform provides useful outputs:

```bash
# Get all outputs
terraform output

# Get specific output
terraform output cloud_run_url
terraform output pubsub_topics
terraform output firestore_database
```

**Example Output:**
```
cloud_run_url = "https://contextpilot-backend-898848898667.us-central1.run.app"
pubsub_topics = [
  "git-events",
  "proposal-events",
  # ... etc
]
firestore_database = "(default)"
```

---

## 🐛 Troubleshooting

### Error: APIs not enabled
```bash
# Enable manually
gcloud services enable run.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Then retry
terraform apply
```

### Error: Firestore already exists
If database already exists, import it:
```bash
terraform import google_firestore_database.database "(default)"
```

### Error: Secret not found
Create the secret first:
```bash
echo -n "placeholder" | gcloud secrets create GOOGLE_API_KEY --data-file=-
terraform apply
```

### Error: Insufficient permissions
Ensure you have Owner or Editor role:
```bash
gcloud projects get-iam-policy contextpilot-hack-4044
```

---

## 💰 Cost Estimation

### Free Tier Usage (Expected for Beta)
- Cloud Run: 2M requests/month FREE
- Pub/Sub: 10GB messages/month FREE
- Firestore: 1GB + 50k reads/day FREE
- Secret Manager: 6 secrets FREE

### Estimated Cost (100 active users)
- **Cloud Run:** $0 (within free tier)
- **Pub/Sub:** $0 (within free tier)
- **Firestore:** $0 (within free tier)
- **Total:** **$0/month** 🎉

### Estimated Cost (1000 active users)
- **Cloud Run:** ~$20/month
- **Pub/Sub:** ~$10/month
- **Firestore:** ~$15/month
- **Total:** ~$45/month

---

## 🎯 For Hackathon Judges

### Why Infrastructure as Code?

**Professional Best Practice:**
- ✅ Reproducible deployments
- ✅ Version controlled infrastructure
- ✅ Easy to scale and modify
- ✅ Self-documenting
- ✅ Disaster recovery ready

**Demo Points:**
> "Our entire production infrastructure is defined as code. Any developer can deploy ContextPilot to their own GCP project with a single command: `terraform apply`. This demonstrates our commitment to scalability and maintainability."

**Show This:**
1. Open `terraform/main.tf` - clean, organized code
2. Run `terraform plan` - show what will be created
3. Run `terraform apply` - deploy in minutes
4. Run `terraform output` - show all resources created
5. **WOW FACTOR:** Delete everything with `terraform destroy` and recreate in minutes!

---

## 📚 Resources

- **Terraform Google Provider:** https://registry.terraform.io/providers/hashicorp/google/latest/docs
- **Google Cloud Run:** https://cloud.google.com/run/docs
- **Terraform Best Practices:** https://www.terraform-best-practices.com/

---

## 🎊 Success Criteria

After deployment, verify:
- [ ] `terraform apply` completes without errors
- [ ] `terraform output cloud_run_url` returns URL
- [ ] Health endpoint returns 200 OK
- [ ] All Pub/Sub topics created
- [ ] Firestore database active
- [ ] Secret Manager has GOOGLE_API_KEY
- [ ] No manual configuration needed!

---

**Status:** ✅ **PRODUCTION READY**  
**Deployment Time:** ~5 minutes  
**Complexity:** ⭐⭐ Beginner-friendly

---

*"Infrastructure as Code - Deploy ContextPilot to any GCP project in minutes!"* 🚀

