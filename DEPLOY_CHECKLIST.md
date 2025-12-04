# 🚀 Production Deployment Checklist

**Quick reference for deploying Receipt Extractor to production**

Use this checklist before EVERY production deployment.

---

## ⚡ PRE-DEPLOYMENT (CRITICAL)

### Security Validation
```bash
# MUST PASS before deploying!
cd /path/to/Web-and-Desktop-Apps
python tools/validate_production_config.py --strict
```

**❌ DO NOT DEPLOY if validation fails!**

---

## 🔒 Security Configuration

- [ ] JWT_SECRET is NOT default value
  - [ ] 64+ characters long
  - [ ] Cryptographically random
  - [ ] Generate: `python -c "import secrets; print(secrets.token_urlsafe(64))"`

- [ ] SECRET_KEY is NOT default value
  - [ ] 32+ characters long
  - [ ] Generate: `python -c "import secrets; print(secrets.token_hex(32))"`

- [ ] FLASK_DEBUG=False
- [ ] DEBUG=False
- [ ] FLASK_ENV=production

---

## 💾 Database

- [ ] Using PostgreSQL (NOT SQLite)
- [ ] DATABASE_URL configured
- [ ] USE_SQLITE=false
- [ ] Migrations run: `cd migrations && alembic upgrade head`
- [ ] Automated backups enabled
- [ ] Backup restore tested

---

## 🌐 Domain & SSL

- [ ] Domain name registered
- [ ] DNS configured (A record or CNAME)
- [ ] SSL certificate active (HTTPS working)
- [ ] CORS_ORIGINS set to production domain
- [ ] HTTP redirects to HTTPS

---

## 💳 Payments (if enabled)

- [ ] Stripe account created
- [ ] Products created in Stripe Dashboard
- [ ] Using LIVE keys (sk_live_*, not sk_test_*)
- [ ] STRIPE_SECRET_KEY configured
- [ ] STRIPE_WEBHOOK_SECRET configured
- [ ] Webhook endpoint tested: `https://yourdomain.com/api/billing/webhook`
- [ ] Test payment processed successfully

---

## 📊 Monitoring

- [ ] Sentry configured (SENTRY_DSN)
- [ ] Uptime monitoring active (UptimeRobot, Pingdom, etc.)
- [ ] Error alerts configured
- [ ] Analytics configured (Google Analytics, Plausible)
- [ ] Log aggregation configured

---

## ✅ Testing

- [ ] All tests passing: `pytest tools/tests/ -v`
- [ ] Complete user journey tested:
  - [ ] Signup
  - [ ] Login
  - [ ] Upload receipt
  - [ ] Extract data
  - [ ] Export results
  - [ ] Upgrade subscription
  - [ ] Cancel subscription

- [ ] Tested on browsers:
  - [ ] Chrome
  - [ ] Firefox
  - [ ] Safari
  - [ ] Edge

- [ ] Tested on mobile:
  - [ ] iOS Safari
  - [ ] Android Chrome

---

## 📋 Legal & Compliance

- [ ] Terms of Service published
- [ ] Privacy Policy published
- [ ] Refund Policy published
- [ ] Cookie consent banner (if EU users)
- [ ] GDPR compliance (if EU users)
  - [ ] Data deletion endpoint
  - [ ] Privacy policy mentions GDPR rights

---

## 🚀 Deployment

- [ ] Code pushed to production branch
- [ ] Environment variables set on platform
- [ ] Database migrations run
- [ ] Application deployed
- [ ] Health check passing: `curl https://yourdomain.com/api/health`
- [ ] No errors in logs

---

## 📣 Post-Deployment

- [ ] Monitor error rate (< 1%)
- [ ] Check performance (response time < 500ms)
- [ ] Verify all endpoints working
- [ ] Test payment processing
- [ ] Customer support email configured
- [ ] Announce launch (Product Hunt, HN, Reddit, etc.)

---

## 🔥 Emergency Rollback Plan

If something goes wrong:

```bash
# 1. Revert to previous deployment
railway rollback  # or equivalent for your platform

# 2. Check logs for errors
railway logs      # or equivalent

# 3. Fix issues in development
# 4. Re-run validation
python tools/validate_production_config.py --strict

# 5. Deploy again
```

---

## 📞 Support Contacts

- **Hosting Platform:** [Railway/Render/AWS support]
- **Database:** [Database provider support]
- **Payments:** Stripe support (support@stripe.com)
- **DNS:** [Domain registrar support]

---

## ⏱️ Estimated Time

- **First deployment:** 4-6 hours
- **Subsequent deployments:** 30-60 minutes

---

## 🎯 Success Metrics (First Week)

- [ ] Uptime > 99.5%
- [ ] Error rate < 1%
- [ ] Response time < 500ms (p95)
- [ ] At least 1 beta user signup
- [ ] Zero critical bugs

---

## 📚 Full Documentation

See [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) for detailed deployment guide.

---

**Last Updated:** $(date '+%Y-%m-%d')

**Status:** Ready for production ✅
