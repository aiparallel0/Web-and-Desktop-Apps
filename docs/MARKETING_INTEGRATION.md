# Marketing Automation Integration Example for app.py

## Add to imports section:

```python
# Marketing automation
try:
    from web.backend.marketing.routes import marketing_bp
    from web.backend.tasks import start_scheduler
    MARKETING_AVAILABLE = True
except ImportError:
    MARKETING_AVAILABLE = False
```

## Register marketing blueprint:

```python
# Register blueprints
if MARKETING_AVAILABLE:
    app.register_blueprint(marketing_bp)
    logger.info("Marketing automation routes registered")
```

## Start background tasks scheduler:

```python
# Start background task scheduler
if os.getenv('ENABLE_EMAIL_AUTOMATION', 'false').lower() == 'true':
    if MARKETING_AVAILABLE:
        scheduler = start_scheduler()
        if scheduler:
            logger.info("Marketing automation scheduler started")
        else:
            logger.warning("Failed to start marketing automation scheduler")
```

## Example: Trigger automation on user signup:

```python
@app.route('/api/auth/register', methods=['POST'])
def register():
    # ... existing registration code ...
    
    # After successful registration
    try:
        from web.backend.marketing.automation import trigger_signup_automation
        from web.backend.database import get_db_context
        
        with get_db_context() as db:
            trigger_signup_automation(user.id, db)
        logger.info(f"Enrolled user {user.id} in welcome sequence")
    except Exception as e:
        logger.error(f"Failed to trigger signup automation: {e}")
    
    return jsonify(result)
```

## Example: Track events:

```python
@app.route('/api/receipts', methods=['POST'])
def upload_receipt():
    # ... existing receipt processing code ...
    
    # Track receipt upload event
    try:
        from web.backend.analytics.tracker import get_tracker
        from web.backend.analytics.events import EventType, EventProperties
        
        tracker = get_tracker()
        tracker.track(
            event_name=EventType.RECEIPT_UPLOADED.value,
            properties={'model_id': model_id},
            user_id=g.user_id
        )
    except Exception as e:
        logger.error(f"Failed to track event: {e}")
    
    return jsonify(result)
```

## Example: Track funnel steps:

```python
@app.route('/api/auth/verify-email', methods=['POST'])
def verify_email():
    # ... existing email verification code ...
    
    # Track funnel step
    try:
        from web.backend.analytics.conversion_funnel import track_funnel_step
        from web.backend.database import get_db_context
        
        with get_db_context() as db:
            track_funnel_step(
                user_id=user.id,
                funnel_type='signup',
                step_name='email_verified',
                db_session=db
            )
    except Exception as e:
        logger.error(f"Failed to track funnel step: {e}")
    
    return jsonify(result)
```

## Example: Trigger subscription automation:

```python
@app.route('/api/billing/webhook', methods=['POST'])
def stripe_webhook():
    # ... handle Stripe webhook ...
    
    if event.type == 'customer.subscription.created':
        # Trigger onboarding sequence
        try:
            from web.backend.marketing.automation import trigger_subscription_automation
            from web.backend.database import get_db_context
            
            with get_db_context() as db:
                trigger_subscription_automation(user_id, db)
            logger.info(f"Enrolled user {user_id} in onboarding sequence")
        except Exception as e:
            logger.error(f"Failed to trigger subscription automation: {e}")
    
    return jsonify({'received': True})
```

## Complete example in app.py:

```python
# Near the top of app.py after other imports
# Marketing automation
MARKETING_AVAILABLE = False
try:
    from web.backend.marketing.routes import marketing_bp
    from web.backend.tasks import start_scheduler
    MARKETING_AVAILABLE = True
    logger.info("Marketing automation modules loaded")
except ImportError as e:
    logger.warning(f"Marketing automation not available: {e}")

# After creating Flask app
app = Flask(__name__)

# ... existing configuration ...

# Register marketing blueprint
if MARKETING_AVAILABLE:
    app.register_blueprint(marketing_bp)
    logger.info("Marketing automation routes registered at /api/marketing")

# ... rest of app.py ...

# At the end, before if __name__ == '__main__':
# Start background scheduler if enabled
scheduler = None
if os.getenv('ENABLE_EMAIL_AUTOMATION', 'false').lower() == 'true' and MARKETING_AVAILABLE:
    scheduler = start_scheduler()
    if scheduler:
        logger.info("Background task scheduler started")
    else:
        logger.warning("Failed to start scheduler")

if __name__ == '__main__':
    try:
        app.run(
            host=os.getenv('FLASK_HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_PORT', 5000)),
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        )
    finally:
        # Shutdown scheduler on app exit
        if scheduler:
            scheduler.shutdown()
            logger.info("Background scheduler stopped")
```
