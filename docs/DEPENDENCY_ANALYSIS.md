================================================================================
DEPENDENCY ANALYSIS REPORT
================================================================================

Total Python modules: 177
Total import relationships: 1146

⚠️  CIRCULAR DEPENDENCIES DETECTED: 1

1. shared → shared

Action Required: Refactor to break circular dependencies

Import Depth Analysis:
  Max depth: 2
  Avg depth: 1.4
  Deepest modules:
    examples.spatial_ocr_usage: depth 2
    tools.verify_mvp_mode: depth 2
    desktop.process_receipt: depth 2
    web.backend.database: depth 2
    web.backend.usage_routes: depth 2

Import Bottlenecks (imported by 10+ modules):
  logging: 100 imports
  typing: 88 imports
  os: 79 imports
  shared: 76 imports
  datetime: 63 imports
  pathlib: 44 imports
  sys: 43 imports
  json: 41 imports
  time: 35 imports
  pytest: 32 imports

Consider: These modules are heavily coupled

Isolated Modules (13):
  migrations
  migrations.versions
  tools.tests
  tools.tests.api
  tools.tests.backend
  tools.tests.circular_exchange
  tools.tests.integration
  tools.tests.shared
  tools.tests.unit
  tools.tests.unit.models
  ... and 3 more
