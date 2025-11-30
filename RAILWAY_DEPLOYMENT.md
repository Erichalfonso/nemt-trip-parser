# Railway Deployment Guide

Deploy your NEMT Parser API to Railway in 5 minutes! 🚂

---

## 🚀 Quick Deployment Steps

### **1. Sign Up for Railway**

Go to: https://railway.app/

- Click "Login with GitHub"
- Authorize Railway to access your GitHub

---

### **2. Create New Project**

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose **`Erichalfonso/nemt-trip-parser`**
4. Railway will auto-detect Python and start building!

---

### **3. Add Environment Variables**

After deployment starts, click on your service, then go to **"Variables"** tab:

Add these variables:

```
GOOGLE_MAPS_API_KEY=AIzaSyDL_J0QL4bIEQGR125JGomiiz376TVhQz0
PARSER_API_KEY=nemt_parser_secret_key_2025
ANTHROPIC_API_KEY=your-claude-key-here (optional)
USE_GEOCODING=true
GEOCODING_PROVIDER=google
```

Click **"Add"** after each variable.

---

### **4. Wait for Deployment**

Railway will:
1. Install dependencies from `requirements.txt`
2. Build your app
3. Start it using `Procfile`
4. Assign a public URL

**Takes ~2-3 minutes**

---

### **5. Get Your API URL**

Once deployed, Railway gives you a URL like:

```
https://nemt-parser-production.up.railway.app
```

Your API endpoint is:
```
https://nemt-parser-production.up.railway.app/api/upload
```

---

## ✅ Test Your Deployment

### **Health Check:**

```bash
curl https://your-app.up.railway.app/health
```

Should return:
```json
{
  "status": "ok",
  "timestamp": "2025-11-29...",
  "version": "1.0.0"
}
```

### **Test Upload:**

```bash
curl -X POST https://your-app.up.railway.app/api/upload \
  -H "X-API-Key: nemt_parser_secret_key_2025" \
  -F "file=@test_file.xlsx"
```

---

## 🔄 Auto-Deploy on Git Push

**Railway automatically redeploys when you push to GitHub!**

```bash
# Make changes
git add .
git commit -m "Update parser"
git push origin main

# Railway automatically:
# - Detects the push
# - Rebuilds the app
# - Deploys new version
# - Zero downtime!
```

---

## 📊 Monitoring

### **View Logs:**

1. Go to Railway dashboard
2. Click your service
3. Click **"Deployments"** tab
4. Click latest deployment
5. Click **"View Logs"**

### **Metrics:**

Railway shows:
- CPU usage
- Memory usage
- Request count
- Response times

---

## 💰 Pricing

### **Hobby Plan ($5/month):**
- Unlimited hours
- 8GB RAM
- 8 vCPU
- Custom domains
- **Perfect for this project!**

### **Free Trial:**
- $5 credit (lasts ~20 days if app runs 24/7)
- Great for testing

---

## ⚙️ Advanced Configuration

### **Custom Domain:**

1. Go to **"Settings"** → **"Domains"**
2. Click **"Generate Domain"** or **"Custom Domain"**
3. Add your domain: `parser.yourcompany.com`
4. Update DNS (Railway gives you instructions)

### **Increase Timeout:**

If parsing large files takes >60 seconds, update `Procfile`:

```
web: gunicorn --workers 4 --timeout 300 --bind 0.0.0.0:$PORT api_server:app
```

(300 = 5 minutes)

### **Add More Workers:**

For higher traffic, increase workers in `Procfile`:

```
web: gunicorn --workers 8 --timeout 120 --bind 0.0.0.0:$PORT api_server:app
```

---

## 🐛 Troubleshooting

### **App won't start:**

1. Check logs in Railway dashboard
2. Verify all environment variables are set
3. Check `requirements.txt` has all dependencies

### **"Application failed to respond":**

- Increase timeout in `Procfile`
- Check logs for errors

### **Geocoding not working:**

- Verify `GOOGLE_MAPS_API_KEY` is set
- Check Google Cloud Console: Geocoding API enabled + billing enabled

---

## 📱 Mobile App / Direct Access

If you want mobile apps or frontend to access the parser directly (not through your website):

### **Enable CORS:**

Already enabled in `api_server.py`:
```python
CORS(app)  # Allows requests from any origin
```

### **Restrict to specific domains (optional):**

```python
CORS(app, origins=["https://yourwebsite.com"])
```

---

## 🔐 Security Checklist

- [ ] API key set in environment variables (not in code)
- [ ] Google Maps API key restricted to Geocoding API only
- [ ] Different API keys for production vs development
- [ ] HTTPS enforced (Railway does this automatically)
- [ ] Monitor logs for suspicious activity

---

## 📈 Scaling

### **Current Setup (Good for 0-10,000 trips/month):**
- 4 Gunicorn workers
- Can handle ~100 requests/second
- Auto-restarts on crashes

### **If you need more (>10,000 trips/month):**

1. **Increase workers:**
   ```
   gunicorn --workers 16 ...
   ```

2. **Upgrade Railway plan:**
   - Pro plan: More CPU/RAM

3. **Add caching:**
   - Add PostgreSQL (free on Railway)
   - Cache geocoding results

---

## 🎯 Post-Deployment Checklist

- [ ] API deployed to Railway
- [ ] Health check endpoint works
- [ ] Test upload with sample file works
- [ ] Environment variables configured
- [ ] Gave API URL to website team
- [ ] Updated `INTEGRATION_GUIDE.md` with real URL
- [ ] Monitoring set up
- [ ] Logs accessible

---

## 📞 Support

**Railway Issues:**
- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway

**Parser Issues:**
- Check GitHub repo
- Contact Erich

---

**You're live on Railway! 🎉**

Your API URL: `https://your-app.up.railway.app/api/upload`

Give this URL to your website team and they can start integrating!
