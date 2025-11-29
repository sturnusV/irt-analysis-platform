# Changelog

All notable changes to IRT AnalyzeR will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-29-11
### Initial Release
**IRT AnalyzeR Platform Launch**

### Added
- **Core IRT Analysis**
  - 3PL IRT modeling with automatic 2PL fallback
  - Maximum likelihood parameter estimation
  - Standard error calculation for all parameters
  - Comprehensive model fit statistics (M₂, TLI, RMSEA, AIC, BIC)

- **Interactive Visualizations**
  - Item Characteristic Curves (ICC) with item selection
  - Item Information Functions (IIF) 
  - Test Information Function (TIF)
  - Real-time interactive charts with Recharts

- **Professional Reporting**
  - Multi-format exports (CSV, PDF)
  - Comprehensive analysis reports
  - Parameter tables with standard errors
  - Model diagnostics and interpretations

- **Platform Features**
  - Drag & drop file upload
  - Real-time progress tracking with Celery
  - Session-based analysis with Redis
  - Responsive Material-UI design
  - Docker containerization

### Technical Architecture
- **Backend**: FastAPI with Python 3.9+
- **Frontend**: React 18 with TypeScript
- **Analysis Engine**: R 4.3+ with mirt package
- **Task Queue**: Celery with Redis broker
- **Deployment**: Docker Compose & Railway-ready

---

## [Unreleased]
### Planned Features
- Multi-group IRT analysis for DIF detection
- Test equating and linking capabilities  
- Computerized Adaptive Testing (CAT) simulation
- User account system for session persistence
- Item bank management system
- API access for programmatic analysis