# Receipt Extractor — Production Deployment

Production sibling of the SROIE fine-tuning research in `aiparallel0/kaggle2`.
The deployed service at **image-to-text.fit** serves the fine-tuned Donut
checkpoint from that repo at scale, behind a real auth, billing, and
observability stack. This README is for researchers verifying that the
deployment is real; it is not a product page.

## What is here

- **Web + Desktop apps.** Flask backend (`web/backend/`), vanilla JS frontend
  (`web/frontend/`), Electron wrapper (`desktop/`).
- **Seven detection algorithms behind one schema.** Tesseract, EasyOCR,
  PaddleOCR, CRAFT, Donut (SROIE/CORD), Florence-2, and a spatial-ensemble
  voter. Every backend returns the unified `DetectionResult` defined in
  `shared/models/schemas.py` (texts, bounding boxes, confidence, model id,
  processing time, error code), so callers never branch on engine.
- **~700 tests.** `pytest tools/tests/` covers shared utils, model adapters,
  backend routes, billing, and integration. The suite enforces the
  no-skip-for-missing-functions rule documented in `docs/TESTING.md`.
- **JWT auth with refresh tokens** (`web/backend/auth.py`), bcrypt password
  hashing, per-route `@require_auth` decorators, rate limiting, and CSP
  headers under `web/backend/security/`.
- **Stripe billing.** Plan definitions, checkout, webhooks, and usage-limit
  middleware live in `web/backend/billing/`.
- **OpenTelemetry.** Traces, metrics, and the CEFR auto-tuning bridge are in
  `web/backend/telemetry/`; extraction latency, error class, and confidence
  are exported per request.
- **Cloud-training adapters.** Pluggable trainers for HuggingFace, Replicate,
  RunPod, and Vast.ai under `web/backend/training/`, sharing the `BaseTrainer`
  interface so retraining can be routed to whichever GPU pool is cheapest.

## Research → Production handoff

The Donut checkpoint fine-tuned on SROIE in the `kaggle2` notebooks is
published to the Hugging Face Hub and pulled here by `shared/models/manager.py`
as the `donut_sroie` model id (the default in `models_config`). The HF
trainer in `web/backend/training/hf_trainer.py` is the same code path used to
produce new checkpoints, so a research run on Kaggle and a production
retrain share configuration. At inference, `shared/models/engine.py` loads
the checkpoint, runs the SROIE-specific JSON parser with a plain-text
fallback, and emits a `DetectionResult` identical to the OCR backends —
making the fine-tuned model a drop-in alternative to classical OCR rather
than a separate pipeline.
