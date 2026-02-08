================================================================================
DEPENDENCY ANALYSIS REPORT
================================================================================

Total Python modules: 219
Total import relationships: 1393

⚠️  CIRCULAR DEPENDENCIES DETECTED: 1

1. shared → shared

Action Required: Refactor to break circular dependencies

Import Depth Analysis:
  Max depth: 2
  Avg depth: 1.4
  Deepest modules:
    test_all_methods: depth 2
    test_integration: depth 2
    test_extraction: depth 2
    validate_deployment: depth 2
    examples.spatial_ocr_usage: depth 2

Import Bottlenecks (imported by 10+ modules):
  logging: 114 imports
  os: 111 imports
  shared: 106 imports
  typing: 103 imports
  sys: 79 imports
  datetime: 67 imports
  pathlib: 55 imports
  json: 54 imports
  time: 45 imports
  pytest: 41 imports

Consider: These modules are heavily coupled

Isolated Modules (16):
  migrations
  migrations.versions
  tools.tests
  tools.tests.api
  tools.tests.backend
  tools.tests.circular_exchange
  tools.tests.integration
  tools.tests.performance
  tools.tests.security
  tools.tests.shared
  ... and 6 more
