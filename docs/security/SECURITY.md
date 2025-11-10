# ContextPilot Security & Cost Protection

## Overview

ContextPilot implements multiple layers of protection against abuse, excessive costs, and security threats.

## 🛡️ Protection Layers

### 1. Rate Limiting (Backend)

**Implementation:** `back-end/app/server.py`

- **Limit:** 100 requests/hour per IP address
- **Window:** Rolling 1-hour window
- **Response:** HTTP 429 (Too Many Requests)
- **Cleanup:** Automatic cleanup of old requests

```python
# Configured in server.py
max_requests = 100
window_seconds = 3600  # 1 hour
```

**Bypass:** Health check endpoint (`/health`) is exempt from rate limiting.

---

### 2. Abuse Detection (Backend)

**Implementation:** `back-end/app/middleware/abuse_detection.py`

**Detects:**
- ✅ **Duplicate requests:** Same request > 20 times in 10 minutes
- ✅ **Bot detection:** User-Agent contains bot/crawler/scraper patterns
- ✅ **Error flooding:** > 50 errors from same IP → Automatic blacklist
- ✅ **Blacklist management:** Persistent blocking of malicious IPs

**Actions:**
- 🔴 **Block (403):** Blacklisted IPs
- 🟡 **Log only:** Suspicious patterns (bots, duplicates)
- 📊 **Monitoring:** All patterns logged for analysis

**Admin Endpoint:**
```bash
curl https://your-backend.run.app/admin/abuse-stats
```

**Response:**
```json
{
  "blacklisted_ips": 2,
  "suspicious_ips": 5,
  "monitored_ips": 150,
  "blacklist": ["1.2.3.4", "5.6.7.8"],
  "suspicious": ["9.10.11.12", "13.14.15.16"]
}
```

---

### 3. Budget Alerts (GCP)

**Implementation:** `terraform/budget.tf`

**Configuration:**
- **Monthly Budget:** $50 USD
- **Alerts at:** 50%, 90%, 100% of budget
- **Notification:** Email to project owner

**Thresholds:**
- 🟢 **$25 (50%):** Warning - Monitor usage
- 🟡 **$45 (90%):** Danger - Investigate immediately
- 🔴 **$50 (100%):** Critical - Take action

**Deploy:**
```bash
cd terraform
terraform apply -var="billing_account_id=YOUR_BILLING_ID"
```

---

### 4. Monitoring & Alerts (GCP)

**Implementation:** `terraform/budget.tf`

**Alerts:**
1. **High Request Rate**
   - Trigger: > 1000 requests/minute on Cloud Run
   - Action: Email notification
   - Purpose: Detect DDoS or viral traffic spike

2. **Rate Limit Errors**
   - Trigger: > 50 rate limit errors (429) in 5 minutes
   - Action: Email notification
   - Purpose: Many users hitting limits (abuse or legitimate surge)

**Dashboard:**
- Cloud Run requests/min
- HTTP response codes (2xx, 4xx, 5xx)
- Gemini API call rate
- Estimated daily cost

**Access Dashboard:**
```bash
# Open GCP Console → Monitoring → Dashboards → "ContextPilot Monitoring"
```

---

## 💰 Cost Protection

### Free Tier Limits (Gemini API)

| Metric | Free Tier Limit | What Happens After |
|--------|----------------|-------------------|
| Requests/minute | 15 RPM | 429 Error (no cost) |
| Requests/day | 1,500 RPD | 429 Error (no cost) |
| Tokens/day | 1M TPD | 429 Error (no cost) |

**With Billing Enabled:**
- Gemini: $0.075 per 1K tokens after free tier
- Cloud Run: $0.40 per 1M requests after 2M/month
- Firestore: $0.06 per 100K reads after 50K/day

### Estimated Costs (Post Free Tier)

**Scenario: 1000 abusive users**
- Daily: ~$93
- Monthly: ~$2,790
- **Mitigation:** Rate limiting prevents this!

---

## 🚨 Emergency Procedures

### If Cost Spike Detected:

1. **Disable Cloud Run Service** (stops all costs immediately)
   ```bash
   gcloud run services update contextpilot-backend \
     --platform managed \
     --region us-central1 \
     --max-instances 0
   ```

2. **Check Abuse Stats**
   ```bash
   curl https://your-backend.run.app/admin/abuse-stats
   ```

3. **Review GCP Logs**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit 100
   ```

4. **Identify & Block Malicious IPs** (if needed, add to firewall)
   ```bash
   # In Cloud Run, you can't block IPs directly
   # But you can add to abuse_detection.py blacklist
   ```

5. **Re-enable with Lower Limits**
   ```bash
   gcloud run services update contextpilot-backend \
     --max-instances 10  # Lower limit
   ```

---

## 🔐 Security Best Practices

### For Hackathon (Current):
- ✅ Rate limiting enabled
- ✅ Abuse detection active
- ✅ Budget alerts configured
- ⚠️ No authentication (public API)

### For Beta Launch:
- 🔐 Implement authentication (API keys or OAuth)
- 🎫 User registration & token management
- 💎 Freemium model (10 proposals/day free)
- 📊 Per-user quotas

### For Production:
- 🔐 Firebase Authentication
- 🎫 JWT tokens with expiration
- 💳 Stripe integration for paid tiers
- 🌍 CloudFlare for DDoS protection
- 🔒 Secret rotation (automated)

---

## 📊 Monitoring Commands

**Check rate limit logs:**
```bash
gcloud logging read "jsonPayload.message=~'Rate limit exceeded'" \
  --limit 50 \
  --format json
```

**Check abuse patterns:**
```bash
gcloud logging read "jsonPayload.message=~'Suspicious pattern'" \
  --limit 50 \
  --format json
```

**Check API costs today:**
```bash
gcloud billing accounts get-iam-policy YOUR_BILLING_ACCOUNT
gcloud alpha billing accounts describe YOUR_BILLING_ACCOUNT --format json
```

---

## 🎯 Current Status

| Protection | Status | Coverage |
|-----------|--------|----------|
| Rate Limiting | ✅ Active | 100 req/hour/IP |
| Abuse Detection | ✅ Active | Blacklist + Patterns |
| Budget Alerts | ⚠️ Pending Deploy | $50/month |
| Monitoring | ⚠️ Pending Deploy | Dashboard + Alerts |
| Authentication | ❌ Not Implemented | Public API |

---

## 📞 Support

If you detect suspicious activity:
1. Check `/admin/abuse-stats` endpoint
2. Review GCP logs
3. Adjust rate limits in `server.py` if needed
4. Contact: [your-email@example.com]

---

**Last Updated:** 2025-10-17  
**Version:** 1.0.0

