# Receipt Extractor Documentation

Complete documentation for the Receipt Extractor SaaS platform.

## Quick Start

New to the project? Start here:

1. [Installation Guide](getting-started/SETUP.md) - Set up your development environment
2. [Quick Deploy Guide](deployment/QUICK_DEPLOY_GUIDE.md) - Deploy to production in 4-6 hours
3. [Project Weaknesses & PR Briefs](PROJECT_WEAKNESSES_AND_PR_BRIEFS.md) - Code quality improvements

## Business Documentation

Planning to launch or monetize the platform:

- [Monetization Guide](MONETIZATION_GUIDE.md) - Step-by-step guide to reach $1,000/month
- [Historical Assessments](archive/) - Archived launch readiness documents

## Technical Documentation

### Core Documentation

- [API Reference](API.md) - Complete REST API documentation
- [User Guide](USER_GUIDE.md) - End-user documentation
- [Deployment Guide](DEPLOYMENT.md) - Multi-platform deployment instructions
- [Roadmap](../ROADMAP.md) - Feature implementation status and future plans

### Development Guides

- [Testing Strategy](development/TESTING_STRATEGY.md) - Testing principles and best practices
- [Code Quality Standards](development/CODE_QUALITY.md) - Quality gates and CI/CD
- [Feature Flags](development/FEATURE_FLAGS_IMPLEMENTATION.md) - Feature flag system

### Architecture

- [CEFR Framework Status](architecture/CEFR_STATUS.md) - Circular Exchange Framework assessment

### Analysis and Reports

- [Repository Analysis](analysis/REPOSITORY_ANALYSIS.md) - Codebase analysis and metrics
- [Repository Screener Reference](analysis/REPOSITORY_SCREENER_QUICK_REF.md) - Quick reference for screening tool

### Project History

- [Changelog](history/CHANGELOG.md) - Complete project history and milestones
- [Telemetry Implementation](TELEMETRY_IMPLEMENTATION_GUIDE.md) - Observability setup

## Feature-Specific Documentation

### Security

- [Telemetry and Security](TELEMETRY_AND_SECURITY.md) - Security and monitoring features

### Features

- [Feature Flags](FEATURE_FLAGS.md) - Available feature flags and configuration
- [Repository Screener](REPOSITORY_SCREENER.md) - Repository analysis tool

## Additional Resources

### External Documentation

- [Flask Documentation](https://flask.palletsprojects.com/) - Web framework
- [PostgreSQL Documentation](https://www.postgresql.org/docs/) - Database
- [Stripe API Reference](https://stripe.com/docs/api) - Payment processing
- [HuggingFace Hub](https://huggingface.co/docs/hub/) - AI models
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/) - Observability

### Development Tools

```bash
# Validate imports
python tools/scripts/validate_imports.py

# Validate environment
python tools/scripts/validate_env.py

# Run tests
./launcher.sh test

# Generate test report
./launcher.sh report
```

## Documentation Organization

```
docs/
├── README.md                              # This file
├── API.md                                 # REST API reference
├── USER_GUIDE.md                          # End-user documentation
├── DEPLOYMENT.md                          # Deployment guide
├── MONETIZATION_GUIDE.md                  # Revenue strategy
├── PROJECT_WEAKNESSES_AND_PR_BRIEFS.md    # Code quality improvement roadmap
├── getting-started/
│   └── SETUP.md                           # Installation and setup
├── deployment/
│   └── QUICK_DEPLOY_GUIDE.md              # Quick deployment guide
├── architecture/
│   └── CEFR_STATUS.md                     # Framework assessment
├── development/
│   ├── TESTING_STRATEGY.md                # Testing guide
│   ├── CODE_QUALITY.md                    # Quality standards
│   └── FEATURE_FLAGS_IMPLEMENTATION.md    # Feature flags
├── analysis/
│   ├── REPOSITORY_ANALYSIS.md             # Codebase analysis
│   └── REPOSITORY_SCREENER_QUICK_REF.md   # Screening tool
├── history/
│   └── CHANGELOG.md                       # Project history
└── archive/
    └── README.md                          # Archived documentation
```

## Getting Help

### Common Issues

1. **Installation Problems**: See [SETUP.md](getting-started/SETUP.md) troubleshooting section
2. **Deployment Issues**: Check [DEPLOYMENT.md](DEPLOYMENT.md) for platform-specific guides
3. **Test Failures**: Review [TESTING_STRATEGY.md](development/TESTING_STRATEGY.md)
4. **Code Quality**: See [CODE_QUALITY.md](development/CODE_QUALITY.md) and [PR Briefs](PROJECT_WEAKNESSES_AND_PR_BRIEFS.md)

### Support Channels

- GitHub Issues: Report bugs and request features
- GitHub Discussions: Ask questions and share ideas
- Documentation: Search this documentation for answers

## Contributing

When contributing to documentation:

1. Keep language clear and beginner-friendly
2. Provide step-by-step instructions
3. Include code examples where applicable
4. Test all commands and procedures
5. Update this index when adding new documents

## Documentation Standards

- No emojis in documentation
- Use clear, professional language
- Make content accessible to beginners
- Provide practical, actionable information
- Include examples and code snippets
- Keep documents focused and well-structured

---

Last Updated: December 31, 2025
Version: 2.1.0
