# Quick Deploy Guide - Get to $1k/Month in 7 Days

**Goal:** Deploy Receipt Extractor to production in the fastest way possible

**Time Required:** 4-6 hours

**Cost:** ~$30-100/month

---

## Day 1: Setup Accounts (2 hours)

### 1. Railway Account
1. Go to https://railway.app
2. Sign up with GitHub
3.  Done - No credit card required for trial

### 2. Stripe Account  
1. Go to https://stripe.com
2. Sign up for account
3. Complete business verification (takes 1-2 business days)
4. **While waiting:** Use test mode for development

### 3. SendGrid Account
1. Go to https://sendgrid.com
2. Sign up (Free tier: 100 emails/day)
3. Create API Key:
   - Settings → API Keys → Create API Key
   - Full Access → Create & View
   - **Copy the key** (shown only once!)

---

## Day 2: Stripe Setup (1 hour)

### Create Products in Stripe Dashboard

1. **Pro Plan:**
   ```
   Products → Create Product
   - Name: Pro Plan
   - Description: 500 receipts/month with advanced features
   - Pricing: $19/month (recurring)
   - Click "Save"
   - COPY the price_id (starts with "price_")
   ```

2. **Business Plan:**
   ```
   Products → Create Product
   - Name: Business Plan
   - Description: 2000 receipts/month for teams
   - Pricing: $49/month (recurring)
   - Click "Save"
   - COPY the price_id (starts with "price_")
   ```

3. **Get API Keys:**
   ```
   Developers → API Keys
   - COPY Publishable key (pk_test_... for now)
   - COPY Secret key (sk_test_... for now)
   - Reveal test key → Copy
   ```

4. **Create Webhook:**
   ```
   Developers → Webhooks → Add Endpoint
   - URL: https://your-app.railway.app/api/billing/webhook (update after deployment)
   - Events: Select all customer.subscription.* and invoice.*
   - Click "Add Endpoint"
   - COPY Signing Secret (whsec_...)
   ```

---

## Day 3: Deploy to Railway (2 hours)

### Step 1: Prepare Your Repository

```bash
# Clone repository (if not already cloned)
git clone https://github.com/aiparallel0/Web-and-Desktop-Apps.git
cd Web-and-Desktop-Apps

# Verify all files are present
ls -la Procfile railway.json Dockerfile
```

### Step 2: Deploy to Railway

1. **Create New Project:**
   ```
   1. Go to railway.app
   2. Click "New Project"
   3. Select "Deploy from GitHub repo"
   4. Choose your repository
   5. Select "main" branch
   6. Click "Deploy"
   ```

2. **Add PostgreSQL Database:**
   ```
   1. In your project, click "New"
   2. Select "Database" → "Add PostgreSQL"
   3. Wait for provisioning (~1 minute)
   4. DATABASE_URL automatically added to environment
   ```

3. **Add Environment Variables:**
   ```
   Click on your service → Variables tab → Raw Editor
   
   Paste this (replace with YOUR values):
   ```

```bash
# Application
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=REPLACE_WITH_64_CHAR_RANDOM_STRING
BASE_URL=https://your-app.railway.app

# Database - Already set by Railway PostgreSQL
# DATABASE_URL is automatically configured

# Authentication
JWT_SECRET=REPLACE_WITH_64_CHAR_RANDOM_STRING
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Stripe (from Day 2)
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
STRIPE_PRICE_ID_PRO=price_YOUR_PRO_PRICE_ID
STRIPE_PRICE_ID_BUSINESS=price_YOUR_BUSINESS_PRICE_ID

# SendGrid (from Day 1)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.YOUR_API_KEY
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Receipt Extractor

# Feature Flags
ENABLE_CEFR=false
USE_SQLITE=false
```

4. **Generate Secrets:**
   ```bash
   # In terminal, run:
   python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48))"
   python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(48))"
   
   # Copy the output and paste into Railway variables
   ```

5. **Deploy:**
   ```
   Click "Deploy" (top right)
   Wait 2-3 minutes for build
   ```

### Step 3: Configure Domain

1. **Get Railway URL:**
   ```
   Settings → Domains
   You'll see: your-app.railway.app
   ```

2. **Update Webhook URL in Stripe:**
   ```
   Go to Stripe Dashboard
   Developers → Webhooks → Click your webhook
   Edit endpoint URL: https://your-app.railway.app/api/billing/webhook
   Save
   ```

3. **Update BASE_URL:**
   ```
   Railway → Variables → BASE_URL
   Change to: https://your-app.railway.app
   Redeploy
   ```

### Step 4: Run Database Migration

```bash
# In Railway dashboard, go to your service
# Click "..." → "Deploy Logs"
# Once deployed, go to Variables → Add New Variable

# Add this ONE-TIME migration trigger:
RUN_MIGRATIONS=true

# Click "Deploy"
# After deployment completes, remove RUN_MIGRATIONS variable
```

---

## Day 4: Testing (1 hour)

### 1. Health Check
```
Visit: https://your-app.railway.app/api/health
Should see: {"status": "healthy", ...}
```

### 2. Register Test User
```
1. Go to: https://your-app.railway.app/register.html
2. Create account with your email
3. Check email for verification link
4. Click verification link
5. Should see "Email verified! Trial activated"
```

### 3. Test Payment Flow
```
1. Go to: https://your-app.railway.app/pricing.html
2. Click "Upgrade to Pro"
3. Use Stripe test card: 4242 4242 4242 4242
4. Expiry: Any future date
5. CVC: Any 3 digits
6. Complete checkout
7. Should redirect to success page
```

### 4. Test Receipt Processing
```
1. Go to: https://your-app.railway.app/index.html
2. Upload a receipt image
3. Click "Extract Text"
4. Should see extracted text
```

### 5. Check Emails
```
Check your inbox for:
- Email verification 
- Welcome email 
- Payment confirmation 
```

---

## Day 5-6: Marketing Setup (Optional)

### Google Analytics (Free)
```
1. Go to analytics.google.com
2. Create account & property
3. Copy Measurement ID (G-XXXXXXXXXX)
4. Add to web/frontend/index.html:

<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Product Hunt Launch
```
1. Create account on producthunt.com
2. Prepare:
   - Logo (512x512px)
   - Screenshots (1270x760px)
   - Description (260 characters)
   - First comment (explain the product)
3. Launch on Tuesday-Thursday for best results
```

### Social Media Announcement
```
Twitter/X:
" Just launched Receipt Extractor!

AI-powered receipt text extraction with 7 OCR models.

 14-day free trial
 $19/month Pro plan
 No credit card required

Try it: https://your-app.railway.app

#SaaS #AI #OCR #ReceiptScanner"

LinkedIn: Same message but more professional tone
Reddit: Post in r/SaaS, r/Entrepreneur (follow community rules)
```

---

## Day 7: Switch to Production (30 minutes)

### When Stripe Verification Completes

1. **Get Live API Keys:**
   ```
   Stripe Dashboard → Toggle "Test mode" to OFF
   Developers → API Keys
   - Copy Live Publishable Key (pk_live_...)
   - Copy Live Secret Key (sk_live_...)
   ```

2. **Update Railway Variables:**
   ```
   STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_KEY
   STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_KEY
   ```

3. **Update Frontend:**
   ```html
   Edit: web/frontend/pricing.html
   Line 15: <meta name="stripe-publishable-key" content="pk_live_YOUR_KEY">
   
   Commit and push:
   git add web/frontend/pricing.html
   git commit -m "Update Stripe live keys"
   git push
   
   Railway will auto-deploy
   ```

4. **Update Webhook:**
   ```
   Stripe Dashboard (LIVE mode)
   Developers → Webhooks → Add Endpoint
   URL: https://your-app.railway.app/api/billing/webhook
   Events: customer.subscription.*, invoice.*
   Copy new Signing Secret
   
   Update Railway variable:
   STRIPE_WEBHOOK_SECRET=whsec_YOUR_LIVE_SECRET
   ```

5. **Test with Real Card:**
   ```
   Use your own card to test
   Subscribe to Pro plan ($19)
   Verify everything works
   Cancel subscription immediately to avoid charges
   ```

---

## Cost Breakdown

### Monthly Costs
```
Railway Starter: $5/month
Railway Pro (recommended): $20/month
PostgreSQL: Included in Railway
SendGrid Free: $0/month (100 emails/day)
Domain (optional): $1.25/month ($15/year)

Total: $5-21/month to start
```

### Break-Even Point
```
Need 1-2 paying customers to cover costs:
- 1 Pro user ($19) = Break-even on Railway Pro
- 2 Pro users ($38) = Profitable

With 10 customers: $190/month revenue - $21 costs = $169 profit
With 50 customers: $950/month revenue - $21 costs = $929 profit
```

---

## Revenue Path to $1k/Month

### Conservative (6 months)
```
Month 1: 50 signups → 10 paid → $190 MRR
Month 2: 50 signups → 20 paid → $380 MRR
Month 3: 50 signups → 30 paid → $570 MRR
Month 4: 50 signups → 40 paid → $760 MRR
Month 5: 50 signups → 50 paid → $950 MRR
Month 6: +3 more → $1,000 MRR 
```

### Optimistic (3 months)
```
With marketing spend ($100/month):
Month 1: 100 signups → 20 paid → $380 MRR
Month 2: 100 signups → 40 paid → $760 MRR
Month 3: 100 signups → 60 paid → $1,140 MRR 
```

### With Referrals
```
10% referral rate compounds growth:
Month 1: 50 signups + 5 referrals = 55
Month 2: 50 signups + 11 referrals = 61
Month 3: 50 signups + 17 referrals = 67
Month 4: 50 signups + 24 referrals = 74
Month 5: 50 signups + 31 referrals = 81
Accelerates to $1k in 4-5 months
```

---

## Next Steps After Launch

### Week 1
- [ ] Monitor error logs daily
- [ ] Respond to support emails within 24h
- [ ] Fix any critical bugs
- [ ] Track conversion metrics

### Month 1
- [ ] Get 10 paying customers
- [ ] Collect user feedback
- [ ] Write 2-3 blog posts
- [ ] Optimize pricing page based on data

### Month 2-3
- [ ] Scale to 30-50 customers
- [ ] Implement feature requests
- [ ] Start paid advertising ($10/day)
- [ ] Build case studies

### Month 4-6
- [ ] Reach $1,000/month MRR
- [ ] Hire VA for customer support
- [ ] Expand marketing channels
- [ ] Plan new features

---

## Troubleshooting

### "Database connection failed"
```bash
Check Railway dashboard:
- PostgreSQL service is running
- DATABASE_URL variable is set
- Try restarting the service
```

### "Emails not sending"
```bash
Check SendGrid dashboard:
- API key is valid
- Sender email is verified
- Check Activity Feed for errors
- Verify EMAIL_FROM matches verified sender
```

### "Stripe checkout not working"
```bash
1. Check browser console for errors
2. Verify STRIPE_PUBLISHABLE_KEY in pricing.html
3. Ensure HTTPS is enabled (Railway provides this)
4. Test with different browser
```

### "Build failing on Railway"
```bash
Check Deploy Logs for errors:
- Python version mismatch → Specify in runtime.txt
- Missing dependencies → Update requirements.txt
- Module not found → Check import paths
```

---

## Support

**Need help?**
- Documentation: `/docs` directory
- GitHub Issues: Report bugs
- Railway Support: help@railway.app
- Stripe Support: https://support.stripe.com

**Emergency Contact:**
If you're stuck and need urgent help, create a GitHub issue with:
1. What you were trying to do
2. What happened instead
3. Error messages
4. Screenshots

---

## Summary

**Total Time:** 4-6 hours spread over 7 days

**Total Cost:** $5-21/month

**Path to $1k/Month:**
1. Deploy (Day 1-3)
2. Test (Day 4)
3. Market (Day 5-7)
4. Acquire customers (Month 1-6)
5. Reach $1,000 MRR 

**The app is ready.** All you need to do is deploy it and tell people about it.

Good luck! 

---

**Last Updated:** 2025-12-09  
**Status:** Ready to deploy
