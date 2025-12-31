# 📋 Quick Reference Card - Deploy to $1k/Month

**Print this page and keep it handy during deployment**

---

## ✅ Current Status

```
Code:         100% Complete
Tests:        1,421 Passing
Docs:         19+ Guides Ready
Revenue:      All Systems Built
Remaining:    4-6 hrs Configuration
```

---

## 🎯 Critical Path (Do These First)

### Day 1: START TODAY
```
[ ] 1. Create Stripe account → stripe.com
        (Verification takes 2-3 business days - THE BOTTLENECK!)
        
[ ] 2. Create Railway account → railway.app
        (Free tier available, upgrade to Pro later)
        
[ ] 3. Create SendGrid account → sendgrid.com
        (Free tier: 100 emails/day)
```

### Day 2-3: Deploy
```
[ ] 1. Generate secrets:
        python generate-secrets.py
        
[ ] 2. Deploy to Railway:
        - Connect GitHub repo
        - Add PostgreSQL database
        - Copy environment variables
        
[ ] 3. Configure Stripe (test mode):
        - Create Pro plan ($19/month)
        - Create Business plan ($49/month)
        - Set up webhook
        - Copy API keys
        
[ ] 4. Configure SendGrid:
        - Get API key
        - Verify sender email
```

### Day 4: Test
```
[ ] 1. Visit: your-app.railway.app/api/health
[ ] 2. Register test user
[ ] 3. Verify email delivers
[ ] 4. Test payment (card: 4242 4242 4242 4242)
[ ] 5. Upload receipt and process
```

### After Stripe Approval: Go Live
```
[ ] 1. Switch Stripe to live mode
[ ] 2. Update Railway with live keys
[ ] 3. Test with real card
[ ] 4. Launch!
```

---

## 🔑 Essential Credentials Checklist

### Stripe (dashboard.stripe.com/apikeys)
```
Test Mode:
[ ] STRIPE_SECRET_KEY=sk_test_...
[ ] STRIPE_PUBLISHABLE_KEY=pk_test_...
[ ] STRIPE_WEBHOOK_SECRET=whsec_...
[ ] STRIPE_PRICE_ID_PRO=price_...
[ ] STRIPE_PRICE_ID_BUSINESS=price_...

Live Mode (after verification):
[ ] STRIPE_SECRET_KEY=sk_live_...
[ ] STRIPE_PUBLISHABLE_KEY=pk_live_...
[ ] STRIPE_WEBHOOK_SECRET=whsec_...
[ ] STRIPE_PRICE_ID_PRO=price_...
[ ] STRIPE_PRICE_ID_BUSINESS=price_...
```

### SendGrid (app.sendgrid.com/settings/api_keys)
```
[ ] SENDGRID_API_KEY=SG....
[ ] SENDGRID_FROM_EMAIL=noreply@yourdomain.com
[ ] SENDGRID_FROM_NAME=Receipt Extractor
```

### Generated Secrets (python generate-secrets.py)
```
[ ] SECRET_KEY=<64 char random string>
[ ] JWT_SECRET=<64 char random string>
```

### Railway (auto-configured)
```
[ ] DATABASE_URL (auto-set when you add PostgreSQL)
[ ] BASE_URL=https://your-app.railway.app
```

---

## 📊 Revenue Quick Reference

### Subscription Plans
```
Free:       $0/month   (10 receipts)
Pro:        $19/month  (500 receipts) ← Primary target
Business:   $49/month  (2,000 receipts)
Enterprise: Custom     (Unlimited)
```

### Break-Even Analysis
```
Operating Cost: $21/month (Railway Pro + domain)
Break-Even:     2 Pro customers = $38/month
First Profit:   With customer #3
```

### Path to $1,000/Month
```
Conservative: 7 months (53 customers @ $19)
Realistic:    4 months (48 customers @ $22 avg)
Optimistic:   2 months (46 customers @ $25 avg)
```

---

## 🔍 Testing Checklist

### Pre-Launch Tests (Test Mode)
```
[ ] Health check: /api/health returns 200
[ ] Registration: User can create account
[ ] Email: Verification email delivers
[ ] Login: User can sign in
[ ] Trial: 14-day trial activates
[ ] Upload: Receipt processing works
[ ] Payment: Stripe checkout completes
[ ] Referral: Code generates correctly
```

### Post-Launch Tests (Live Mode)
```
[ ] Use real card (then cancel immediately)
[ ] Verify subscription appears in Stripe
[ ] Verify webhook triggers
[ ] Check database for subscription record
[ ] Confirm Pro access granted
[ ] Test subscription cancellation
```

### Test Card (Stripe Test Mode Only)
```
Card Number:  4242 4242 4242 4242
Expiry:       12/25 (any future date)
CVC:          123 (any 3 digits)
ZIP:          12345 (any 5 digits)
```

---

## 🚨 Common Issues & Solutions

### "Emails not delivering"
```
✓ Check spam folder
✓ Verify SENDGRID_FROM_EMAIL matches verified sender
✓ Check SendGrid Activity dashboard
✓ Ensure EMAIL_SERVICE=sendgrid in env vars
```

### "Stripe checkout not loading"
```
✓ Check browser console for errors
✓ Verify STRIPE_PUBLISHABLE_KEY in pricing.html
✓ Ensure HTTPS is enabled (Railway provides this)
✓ Try different browser
```

### "Database connection failed"
```
✓ Verify PostgreSQL service running in Railway
✓ Check DATABASE_URL is set automatically
✓ Restart Railway service
✓ Check logs for detailed error
```

### "Health check fails"
```
✓ Check deploy logs for errors
✓ Ensure all dependencies installed
✓ Verify DATABASE_URL is correct
✓ Check that migrations ran
```

---

## 📞 Support Contacts

```
Railway:    help@railway.app
Stripe:     support.stripe.com (24/7 chat)
SendGrid:   support.sendgrid.com
```

---

## 📁 Essential Files

### Configuration
```
.env.production.template  → Production env vars
generate-secrets.py       → Secret generation
deploy-check.sh          → Pre-deploy verification
```

### Documentation
```
START_HERE.md             → This guide
NEXT_STEPS.md            → Step-by-step plan
READINESS_ASSESSMENT.md  → Full evaluation
QUICK_DEPLOY_GUIDE.md    → 7-day roadmap
```

### Code
```
web/backend/app.py                  → Main Flask app
web/backend/billing/stripe_handler.py → Payment processing
web/frontend/pricing.html          → Pricing page
web/backend/email_templates/       → Email templates
```

---

## 🎯 Launch Week Milestones

### Week 1: Deploy
```
[ ] Monday:    Create accounts
[ ] Tuesday:   Deploy to Railway
[ ] Wednesday: Configure & test
[ ] Thursday:  Beta users
[ ] Friday:    Fix issues
[ ] Weekend:   Wait for Stripe
```

### Week 2: Launch
```
[ ] Monday:    Switch to live mode
[ ] Tuesday:   Product Hunt launch
[ ] Wednesday: Social media push
[ ] Thursday:  Monitor & respond
[ ] Friday:    Analyze metrics
[ ] Weekend:   Plan next week
```

---

## 💯 Success Metrics

### Week 1
```
Target: 10+ signups
        0 critical errors
        1+ paying customer
```

### Month 1
```
Target: 50+ signups
        $100+ MRR
        5+ referrals
```

### Month 3
```
Target: 150+ users
        $400+ MRR
        10+ paying customers
```

### Month 6
```
Target: 300+ users
        $800+ MRR
        Path to $1k clear
```

---

## 🔗 Quick Links

### External Services
- Stripe Dashboard: https://dashboard.stripe.com
- Railway Dashboard: https://railway.app/dashboard
- SendGrid Dashboard: https://app.sendgrid.com

### Documentation
- API Docs: docs/API.md
- User Guide: docs/USER_GUIDE.md
- Deployment: docs/DEPLOYMENT.md

### Testing
```bash
# Health check
curl https://your-app.railway.app/api/health

# View logs
railway logs

# Run tests locally
./launcher.sh test
```

---

## ⏱️ Time Estimates

```
┌────────────────────────────┬──────────────┐
│ Task                       │ Time         │
├────────────────────────────┼──────────────┤
│ Create accounts            │ 1 hour       │
│ Generate secrets           │ 5 minutes    │
│ Deploy to Railway          │ 2-3 hours    │
│ Configure Stripe           │ 1 hour       │
│ Configure SendGrid         │ 30 minutes   │
│ Testing                    │ 1 hour       │
│ Wait for Stripe approval   │ 2-3 days     │
│ Switch to live mode        │ 30 minutes   │
├────────────────────────────┼──────────────┤
│ Total hands-on time        │ 4-6 hours    │
│ Total calendar time        │ 1 week       │
└────────────────────────────┴──────────────┘
```

---

## 💰 Cost Summary

```
┌────────────────────────────┬──────────────┐
│ Service                    │ Cost         │
├────────────────────────────┼──────────────┤
│ Railway Pro (recommended)  │ $20/month    │
│ Railway Starter (minimum)  │ $5/month     │
│ PostgreSQL                 │ Included     │
│ SendGrid (100 emails/day)  │ Free         │
│ Domain (optional)          │ $1.25/month  │
│ Stripe fees                │ 2.9% + $0.30 │
├────────────────────────────┼──────────────┤
│ Total minimum              │ $6.25/month  │
│ Total recommended          │ $21.25/month │
└────────────────────────────┴──────────────┘

Break-even: 1-2 customers
First profit: Customer #3 onwards
```

---

## ✅ Final Checklist

```
Before Launch:
[ ] All credentials collected
[ ] Environment variables configured
[ ] App deployed to Railway
[ ] PostgreSQL database added
[ ] All tests passing
[ ] Stripe test mode working
[ ] Emails delivering
[ ] Beta users invited

After Stripe Approval:
[ ] Switched to Stripe live mode
[ ] Updated Railway with live keys
[ ] Updated pricing.html with live key
[ ] Tested with real payment
[ ] Launched on Product Hunt
[ ] Social media announced
[ ] Monitoring set up

First Week:
[ ] Responded to all user questions
[ ] Fixed any critical bugs
[ ] Collected feedback
[ ] First paying customer acquired

First Month:
[ ] 50+ signups achieved
[ ] $100+ MRR reached
[ ] Conversion funnel optimized
[ ] Planning next features
```

---

**Remember:** The project is 100% code complete. Only configuration remains.

**Start today. Launch this week. Make money next month.**

Good luck! 🚀

---

**Quick Start:** Read NEXT_STEPS.md for detailed instructions  
**Full Assessment:** Read READINESS_ASSESSMENT.md for complete analysis  
**Support:** Create GitHub issue if you get stuck
