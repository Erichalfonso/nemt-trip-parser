# Railway Deployment Guide

Deploy the NEMT Trip Parser API to Railway.

---

## Deployment Steps

### 1. Sign Up

Go to [railway.app](https://railway.app/) and log in with GitHub.

### 2. Create Project

1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Choose your `nemt-trip-parser` repository
4. Railway auto-detects Python and begins building

### 3. Set Environment Variables

In the Railway dashboard, go to your service > **Variables** tab. Add:

```
API_KEY=<your-secure-api-key>
GOOGLE_MAPS_API_KEY=<your-google-maps-key>
ANTHROPIC_API_KEY=<your-claude-key>
USE_GEOCODING=true
GEOCODING_PROVIDER=google
```

### 4. Wait for Build

Railway will:
1. Install dependencies from `requirements.txt`
2. Build the app
3. Start it using the `Procfile`
4. Assign a public URL

Build time is approximately 2-3 minutes.

### 5. Get Your URL

Once deployed, Railway provides a URL like:

```
https://nemt-parser-production.up.railway.app
```

Your API endpoint will be:

```
https://nemt-parser-production.up.railway.app/api/upload
```

---

## Verify Deployment

### Health check

```bash
curl https://your-app.up.railway.app/health
```

Expected response:

```json
{
  "status": "ok",
  "timestamp": "2025-11-29...",
  "version": "1.0.0"
}
```

### Test upload

```bash
curl -X POST https://your-app.up.railway.app/api/upload \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -F "file=@test_file.xlsx"
```

---

## Auto-Deploy

Railway automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update parser"
git push origin main
# Railway detects the push, rebuilds, and deploys with zero downtime
```

---

## Monitoring

### Logs

1. Open the Railway dashboard
2. Click your service
3. Go to **Deployments** tab
4. Click the latest deployment
5. Click **View Logs**

### Metrics

Railway provides CPU usage, memory usage, request count, and response time metrics in the dashboard.

---

## Pricing

**Hobby Plan ($5/month):** Unlimited hours, 8 GB RAM, 8 vCPU, custom domains. Suitable for most workloads.

**Free Trial:** $5 credit, sufficient for approximately 20 days of continuous operation.

---

## Advanced Configuration

### Custom domain

1. Go to **Settings** > **Domains**
2. Click **Generate Domain** or **Custom Domain**
3. Follow the DNS instructions Railway provides

### Increase timeout

For large files that take over 60 seconds, update the `Procfile`:

```
web: gunicorn --workers 4 --timeout 300 --bind 0.0.0.0:$PORT api_server:app
```

### Increase workers

For higher traffic:

```
web: gunicorn --workers 8 --timeout 120 --bind 0.0.0.0:$PORT api_server:app
```

---

## Troubleshooting

**App won't start:**
- Check logs in the Railway dashboard
- Verify all environment variables are set
- Confirm `requirements.txt` includes all dependencies

**"Application failed to respond":**
- Increase timeout in `Procfile`
- Check logs for errors

**Geocoding not working:**
- Verify `GOOGLE_MAPS_API_KEY` is set
- Confirm the Geocoding API is enabled in Google Cloud Console with billing active

---

## Scaling

**Current setup (suitable for up to 10,000 trips/month):**
- 4 Gunicorn workers
- Handles approximately 100 requests/second
- Auto-restarts on crashes

**Higher volume (10,000+ trips/month):**
1. Increase workers: `gunicorn --workers 16 ...`
2. Upgrade to Railway Pro plan for more CPU/RAM
3. Add geocoding result caching

---

## Security Checklist

- [ ] API key set via environment variables (not in code)
- [ ] Google Maps API key restricted to Geocoding API only
- [ ] Separate API keys for production and development
- [ ] HTTPS enforced (Railway handles this automatically)
- [ ] Monitor logs for unusual activity

---

Back to [README](README.md).
