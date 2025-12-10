# Marketing Automation Guide

## Overview

Receipt Extractor's marketing automation system provides comprehensive email sequences, event tracking, and conversion funnel analysis to drive user engagement and conversions.

## Features

### 1. Email Sequences

Four automated email sequences help guide users through their journey:

#### Welcome Series (3 emails over 7 days)
- **Day 0**: Welcome email with getting started guide
- **Day 3**: Feature highlights and use case examples  
- **Day 7**: Trial ending reminder with upgrade CTA

#### Trial Conversion Series (5 emails over 14 days)
- **Day 1**: Account setup confirmation
- **Day 5**: Feature introduction ("Have you tried X?")
- **Day 10**: Trial ending in 4 days
- **Day 13**: Last day reminder
- **Day 15**: Trial ended with special offer

#### Onboarding Series (4 emails over 30 days)
- **Day 0**: Thank you for subscribing
- **Day 2**: API documentation and integration guide
- **Day 7**: Advanced features walkthrough
- **Day 30**: Check-in and feedback request

#### Re-engagement Series (3 emails over 90 days)
- **Day 30**: "We miss you" with new features
- **Day 60**: Special discount offer (20% off)
- **Day 90**: Final reminder before deactivation

### 2. Event Tracking

Track 40+ standard events throughout the user lifecycle:

**User Events:**
- Signup, login, email verification
- Onboarding progression
- Trial start/end

**Engagement Events:**
- Receipt uploads and processing
- API usage
- Feature usage (models, cloud storage, training)

**Conversion Events:**
- Pricing page views
- Upgrade clicks
- Checkout and payments
- Subscription changes

**Churn Events:**
- Inactivity milestones (30/60/90 days)
- Account cancellations

### 3. Conversion Funnels

Four conversion funnels track user progression:

#### Signup Funnel
`Landing Page → Signup Click → Account Created → Email Verified → Trial Started`

#### Activation Funnel
`Trial Started → First Receipt → First API Call → 5+ Receipts`

#### Conversion Funnel
`Trial Started → Upgrade Prompt → Pricing Page → Checkout → Subscription`

#### Retention Funnel
`Subscription → Month 1 Active → Month 2 Active → Month 3 Active`

## Configuration

### Environment Variables

```bash
# Email Service
EMAIL_SERVICE=sendgrid              # or mailgun, mock
ENABLE_EMAIL_AUTOMATION=true

# SendGrid
SENDGRID_API_KEY=SG.xxx
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=Receipt Extractor

# Mailgun
MAILGUN_API_KEY=xxx
MAILGUN_DOMAIN=mg.yourdomain.com

# Analytics
ENABLE_ANALYTICS_TRACKING=true
ENABLE_CONVERSION_TRACKING=true

GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
MIXPANEL_TOKEN=xxx
SEGMENT_WRITE_KEY=xxx
```

### Background Tasks

The system uses APScheduler for background job processing:

```bash
# Install APScheduler
pip install apscheduler

# Tasks run automatically when app starts
# - Email sending: Every hour
# - Analytics processing: Every 5 minutes
```

## API Endpoints

### Event Tracking

```http
POST /api/marketing/track-event
Content-Type: application/json

{
  "event": "receipt_uploaded",
  "properties": {
    "model_id": "ocr_tesseract",
    "processing_time": 1.5
  },
  "user_id": "uuid",
  "session_id": "session-123"
}
```

### Email Management

**Subscribe to sequence:**
```http
POST /api/marketing/email/subscribe

{
  "user_id": "uuid",
  "sequence_type": "welcome"
}
```

**Unsubscribe:**
```http
POST /api/marketing/email/unsubscribe

{
  "user_id": "uuid",
  "sequence_type": "welcome"
}
```

**Get preferences:**
```http
GET /api/marketing/email/preferences?user_id=uuid
```

**Update preferences:**
```http
PUT /api/marketing/email/preferences

{
  "user_id": "uuid",
  "sequence_type": "welcome",
  "paused": true
}
```

### Admin Endpoints

**Analytics dashboard:**
```http
GET /api/admin/analytics/dashboard?days=30
```

**List campaigns:**
```http
GET /api/admin/marketing/campaigns
```

**Send campaign:**
```http
POST /api/admin/marketing/send-campaign

{
  "user_ids": ["uuid1", "uuid2"],
  "template_name": "welcome_day0.html",
  "subject": "Welcome!",
  "test_mode": false
}
```

## Integration

### Backend Integration

**Trigger automation on user signup:**

```python
from web.backend.marketing.automation import trigger_signup_automation
from web.backend.database import get_db_context

with get_db_context() as db:
    trigger_signup_automation(user_id, db)
```

**Track events:**

```python
from web.backend.analytics.tracker import get_tracker
from web.backend.analytics.events import EventType, EventProperties

tracker = get_tracker()
tracker.track(
    event_name=EventType.RECEIPT_PROCESSED.value,
    properties=EventProperties.receipt_processed(
        model_id='ocr_tesseract',
        processing_time=1.5,
        confidence=0.95
    ),
    user_id=user_id
)
```

**Track funnel step:**

```python
from web.backend.analytics.conversion_funnel import track_funnel_step
from web.backend.database import get_db_context

with get_db_context() as db:
    track_funnel_step(
        user_id=user_id,
        funnel_type='signup',
        step_name='email_verified',
        db_session=db
    )
```

### Frontend Integration

**Add analytics script to HTML:**

```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>

<!-- Mixpanel -->
<script src="https://cdn.mxpnl.com/libs/mixpanel-2-latest.min.js"></script>
<script>
  mixpanel.init('YOUR_TOKEN');
</script>

<!-- Internal Analytics -->
<script src="/js/analytics.js"></script>
```

**Track events from JavaScript:**

```javascript
// Track custom event
Analytics.track('upgrade_button_clicked', {
  plan: 'pro',
  location: 'pricing_page'
});

// Track button click
document.getElementById('signup-btn').addEventListener('click', function() {
  Analytics.trackClick(this, 'signup_button_clicked');
});

// Identify user after login
Analytics.identify(userId);
```

**Add tracking attributes to HTML:**

```html
<!-- Auto-track clicks -->
<button data-track data-track-event="pricing_viewed">
  View Pricing
</button>

<!-- Auto-track form submissions -->
<form data-track-submit data-track-event="contact_form_submitted">
  <!-- form fields -->
</form>
```

## Email Templates

### Creating Templates

Templates are stored in `web/backend/email_templates/marketing/`.

**Template structure:**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Title</title>
    <style>
        /* Mobile-responsive styles */
    </style>
</head>
<body>
    <div class="container">
        <h1>Hello {{user_name}}!</h1>
        <p>Your plan: {{current_plan}}</p>
        
        <a href="https://yourdomain.com/dashboard">
            Get Started
        </a>
        
        <p><a href="{{unsubscribe_link}}">Unsubscribe</a></p>
    </div>
</body>
</html>
```

**Available template variables:**
- `{{user_name}}` - User's full name or email prefix
- `{{user_email}}` - User's email address
- `{{company_name}}` - User's company
- `{{current_plan}}` - User's subscription plan
- `{{unsubscribe_link}}` - Unsubscribe URL

### Template Best Practices

1. **Mobile-first**: Design for mobile, enhance for desktop
2. **Plain text fallback**: Always include plain text version
3. **Clear CTAs**: One primary call-to-action per email
4. **Unsubscribe link**: Required for GDPR compliance
5. **Personalization**: Use merge tags for user data
6. **A/B testing**: Test subject lines and content

## Analytics Dashboard

Access the admin dashboard at `/api/admin/analytics/dashboard`:

**Metrics included:**
- Total users in each funnel
- Conversion rates per step
- Drop-off rates
- Overall funnel completion
- Time period analysis

**Example response:**

```json
{
  "period_days": 30,
  "funnels": {
    "signup": {
      "total_users": 1000,
      "users_completed": 450,
      "overall_conversion_rate": 45.0,
      "steps": [
        {
          "step_name": "landing_page_view",
          "users_completed": 1000,
          "conversion_rate": 100.0,
          "drop_off_rate": 0
        },
        {
          "step_name": "signup_click",
          "users_completed": 700,
          "conversion_rate": 70.0,
          "drop_off_rate": 30.0
        }
      ]
    }
  }
}
```

## Privacy & Compliance

### GDPR Compliance

1. **Opt-in required**: Users must explicitly opt-in to emails
2. **Unsubscribe**: Easy one-click unsubscribe in every email
3. **Data export**: Users can request their data
4. **Data deletion**: Users can request account deletion
5. **Cookie consent**: Analytics require consent

### Email Compliance

- Include physical mailing address
- Respect unsubscribe requests within 10 days
- Use accurate subject lines
- Identify commercial emails
- Monitor bounce rates and complaints

## Troubleshooting

### Emails not sending

1. Check `EMAIL_SERVICE` environment variable
2. Verify API keys are correct
3. Check background task scheduler is running
4. Review email logs in database

### Events not tracking

1. Verify `ENABLE_ANALYTICS_TRACKING=true`
2. Check frontend analytics.js is loaded
3. Inspect browser console for errors
4. Verify API endpoint is accessible

### Funnel metrics incorrect

1. Ensure funnel steps are tracked in correct order
2. Check database for ConversionFunnel entries
3. Verify date range parameters
4. Review user_id consistency

## Best Practices

1. **Segment users**: Send relevant content based on user behavior
2. **Test emails**: Always test before sending to users
3. **Monitor metrics**: Track open rates, click rates, conversions
4. **A/B test**: Test subject lines, content, timing
5. **Clean lists**: Remove inactive users periodically
6. **Respect preferences**: Honor unsubscribe requests immediately
7. **Optimize timing**: Send emails at optimal times
8. **Mobile optimize**: Ensure emails look good on mobile
9. **Track ROI**: Calculate LTV:CAC ratio
10. **Iterate**: Continuously improve based on data

## Support

For questions or issues:
- Review logs: `logs/app.log`
- Check database: `EmailLog`, `AnalyticsEvent` tables
- API documentation: `/docs/API.md`
- Email templates: `web/backend/email_templates/marketing/`
