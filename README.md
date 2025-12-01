# 🌟 IRT AnalyzeR: The Modern IRT Analysis Platform

A modern, web-based platform for **Item Response Theory (IRT)** analysis with real-time visualization and comprehensive professional reporting.

![IRT Analysis Platform](https://img.shields.io/badge/IRT-AnalyzeR-blue)
![Python 3.11](https://img.shields.io/badge/Python-3.9-green)
![R 4.3+](https://img.shields.io/badge/R-4.3-orange)
![FastAPI 0.104+](https://img.shields.io/badge/FastAPI-0.104-lightblue)
![React 18+](https://img.shields.io/badge/React-18-61dafb)
![Redis](https://img.shields.io/badge/Redis-StorageBroker-red)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Microservices](https://img.shields.io/badge/Architecture-Microservices-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

____

## Quick Demo

Try the platform with sample data:
1. Use the built-in sample data button to run the analysis.
2. See real-time IRT analysis in action!

## Key Features

### Core Analysis
* **3PL IRT Modeling** with automatic fallback to **2PL** when insufficient data for guessing parameter ($c$) estimation is present.
* **Real-time parameter estimation** with standard errors (SEs).
* **Comprehensive Model Fit Statistics** ($M_2$, TLI, RMSEA, AIC, BIC).
* **Automated data validation** and cleaning.

### Interactive Visualizations
The platform generates high-quality, interactive plots to interpret results: 
* **Item Characteristic Curves (ICC)**: Probability curves showing the expected outcome for each item across different ability ($\theta$) levels.
* **Item Information Functions (IIF)**: Curves illustrating the information (precision) provided by each item across the ability continuum.
* **Test Information Function (TIF)**: The overall precision and standard error of measurement for the entire test.
* Interactive charts with **item selection** and **tooltips**.

### Professional Reporting
* Multiple export formats: **CSV, PDF**, and **JSON**.
* Comprehensive analysis reports with **interpretations**.
* Parameter tables with estimated values and **standard errors**.
* Model diagnostics and fit statistics.

### User Experience
* **Drag & drop file upload** for instant data import.
* **Real-time progress tracking** during lengthy analysis.
* **Responsive design** for desktop and mobile access.
* **Session-based analysis** with automatic cleanup for privacy.

## Sample Output

The platform delivers detailed analysis including:

* **Item Parameters**: Discrimination (**a**), Difficulty (**b**), Guessing (**c**) with standard errors.
* **Model Fit**: $M_2$, TLI, RMSEA, and reliability indices.
* **Visualizations**: ICC, IIF, and TIF curves.
* **Exportable Results**: Professional reports in multiple formats.

## Technology Stack

IRT AnalyzeR utilizes a robust, scalable microservices architecture.

### Backend
| Service | Role | Exposed Port |
| :--- | :--- | :--- |
| **backend** | Main application logic powered by **FastAPI** | 8000 |
| **frontend** | User interface built with **React** | 3000 |
| **r-service** | Dedicated **R analysis service** | 8001 |
| **redis** | Session storage and message broker | 6379 |
| **celery-worker** | Background processing of IRT tasks | N/A |

### Frontend
| Technology | Role |
| :--- | :--- |
| **React 18** | Modern UI framework for a dynamic user experience. |
| **Material-UI (MUI)** | Component library for a polished, professional look. |
| **Recharts** | Interactive library for data visualization (ICC, IIF, TIF). |
| **TypeScript** | Ensures type-safe and maintainable development. |

### Deployment Ready
* **Docker Compose** for local development.
* **Cloud storage compatible** for result persistence (if configured).
* **Scalable architecture** leveraging task queues and microservices.

## Quick Start

### Prerequisites
* **Docker** and **Docker Compose**

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/sturnusV/irt-analysis-platform.git](https://github.com/sturnusV/irt-analysis-platform.git)
    cd irt-analysis-platform
    ```
2.  **Start the application:**
    ```bash
    docker-compose up -d
    ```

### Access the Application
* **Frontend (User Interface):** `http://localhost:3000`
* **Backend API:** `http://localhost:8000`
* **API Documentation (Swagger UI):** `http://localhost:8000/docs`

### Using the Platform
1.  **Upload your data** (CSV file with binary responses).
2.  **Monitor progress** with real-time status updates during analysis.
3.  **Explore results** via interactive charts and parameter tables.
4.  **Export reports** in your preferred format.

## Data Format

The platform requires data in a standard dichotomous format.

### Required CSV Format
* **Rows**: Students/respondents
* **Columns**: Items (questions)
* **Values**: `0` (incorrect) or `1` (correct)
* *Optional*: The first column can be dedicated to student IDs.

### Example CSV
```csv
student_id,item1,item2,item3,item4
student001,1,0,1,1
student002,0,1,1,0
student003,1,1,0,1
```

## Configuration

### Environment Variables
Key variables can be configured via an `.env` file:

```env
REDIS_URL=redis://redis:6379
R_SERVICE_URL=http://r-service:8001
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

## Docker Services

This table outlines the core microservices running within the Dockerized environment for **IRT AnalyzeR**:

| Service | Role | Exposed Port |
| :--- | :--- | :--- |
| **backend** | The main application logic powered by **FastAPI**. | 8000 |
| **frontend** | The user interface built with **React**. | 3000 |
| **r-service** | Dedicated **R analysis service** (using `mirt` and `plumber`). | 8001 |
| **redis** | Used for **session storage** and as a **message broker** for Celery. | 6379 |
| **celery-worker** | Handles the **background processing** of heavy IRT analysis tasks. | N/A |

## Data Privacy & Expiration

**IRT AnalyzeR** is designed for ephemeral processing, prioritizing user privacy.

### Automatic Cleanup ⏰
* Analysis results **expire after 1 hour**.
* All data is automatically purged from Redis after expiration.
* **No long-term storage** of user data.
* Ephemeral processing: files are processed and removed.

### Privacy Features
* **Session-based analysis** (no user accounts required).
* No persistent storage of uploaded files.
* Automatic cleanup prevents data accumulation.
* Cloud-ready with configurable, *optional* storage backends for advanced users.

## Planned Features (Roadmap)

### Short-term Roadmap
* **Multi-group IRT analysis** for Differential Item Functioning (DIF).
* **Test equating and linking** between different test forms.
* Computerized Adaptive Testing (**CAT**) simulation.
* Differential Item Functioning (**DIF**) detection.
* Item bank management with import/export capabilities.

### Medium-term Enhancements
* User accounts for saving analysis sessions.
* Collaborative workspaces for research teams.
* Advanced visualization with 3D parameter spaces.
* API access for programmatic analysis.
* Plugin system for custom IRT models.

### Long-term Vision
* Real-time CAT administration.
* Machine learning integration for parameter priors.
* Multi-dimensional IRT models.
* Bayesian estimation methods.
* Educational dashboard for institutional use.

## Architecture

### Microservices Design
```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │◄──► │   Backend   │◄──► │  R Service  │
│   (React)   │     │  (FastAPI)  │     │   (mirt)    │
└─────────────┘     └─────────────┘     └─────────────┘
                          │                   │
                          ▼                   │
                    ┌─────────────┐           │
                    │   Redis     │◄──────────┘
                    │  (Broker)   │
                    └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │   Celery    │
                    │   Worker    │
                    └─────────────┘
```

### Analysis Pipeline
1.  **File Upload & Validation** → Data cleaning and format checking
2.  **IRT Model Fitting** → 3PL with 2PL fallback in R
3.  **Parameter Estimation** → Maximum likelihood estimation with SEs
4.  **Visualization Generation** → ICC, IIF, and TIF curves
5.  **Report Compilation** → Comprehensive exportable results

## Development

### Local Development Setup
To set up individual services locally without Docker:

```bash
# Backend development
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development  
cd frontend
npm install
npm run dev

# R service development
cd r_service
R -e "install.packages(c('plumber','mirt','jsonlite','dplyr','purrr'))"
R -e "pr <- plumber::plumb('plumber.R'); pr$run(port=8001)"
```

### Running Tests

```Bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up
```
## License

This project is licensed under the **MIT License** - see the `LICENSE` file for details.

## Acknowledgments

* **mirt R package** by Phil Chalmers for robust IRT estimation.
* **FastAPI** team for the excellent web framework.
* **Material-UI** team for the React component library.
* **Redis** for reliable session storage and task queuing.