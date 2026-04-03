#  AI Quant Portfolio Dashboard
**Live Agentic S&P 500 Sector Rotation Insights based on K-Means Macro Clustering**


![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?logo=streamlit&logoColor=white)
![Azure](https://img.shields.io/badge/Deployed_on-Azure_App_Service-0089D6?logo=microsoft-azure&logoColor=white)
![Status](https://img.shields.io/badge/Status-Production-success)

A quantitative portfolio dashboard designed to synthesize macroeconomic data, technical indicators, and AI-driven thesis generation. This platform identifies market regimes (Risk-On, Risk-Off, Sideways) and provides actionable sector rotation and risk management protocols using Agentic AI.

##  Key Features

* **Macro Regime Clustering:** Utilizes K-Means clustering to classify the current market environment based on volatility, inflation (CPI), and broad market returns.
* **Agentic Decision Engine:** Integrates with Google Gemini to dynamically generate JSON-formatted investment theses, sector upgrade/downgrade signals, and risk management protocols based on live data.
* **Advanced Technical Analytics:** Interactive Plotly visualizations for stock peer analysis and technical health indicators (50/200 SMAs, MACD, RSI).
* **Cloud-Native Architecture:** Fully decoupled, modular functional architecture securely connected to an Azure SQL Database using Azure Active Directory (Managed Identity).
* **Enterprise UI/UX:** Custom CSS styling, responsive KPI metric cards, and a dynamic Light/Dark mode implementation overriding Streamlit's default aesthetics.

##  System Architecture & Technology Stack

| Category | Technologies |
| :--- | :--- |
| **Frontend & Core** | Python 3.11, Streamlit, Plotly, Custom CSS |
| **AI & Analytics** | Google Gemini, Scikit-Learn, Pandas, Numpy |
| **Cloud Infrastructure** | Azure App Service, Azure SQL Database, GitHub Actions (CI/CD) |
| **Data Pipelines** | Yahoo Finance, FRED API, PyODBC, SQLAlchemy |

##  Repository Structure

The application follows a modern functional architecture, separating the UI from business logic and data ingestion.

```text
quant-portfolio-dashboard/
│
├── .github/workflows/   # CI/CD pipelines for Azure deployment
├── .streamlit/          # Streamlit theme configuration (config.toml)
│
├── src/                 # Core Application Modules
│   ├── analytics.py     # Quantitative math & technical indicator logic
│   ├── charts.py        # Plotly graph generation
│   ├── components.py    # Static UI rendering & HTML injection
│   ├── data_handler.py  # Azure SQL connections & data sanitization
│   ├── mock_data.py     # Synthetic data generator for offline testing
│   └── style.css        # Enterprise dashboard styling
│
├── app.py               # Main Streamlit Controller (Entry Point)
└── requirements.txt     # Python dependencies
```

##  Local Development & Testing
You can run this dashboard locally without needing access to the live Azure SQL database by utilizing the built-in mock data generator.

### 1. Clone the repository

```Bash
git clone [https://github.com/MSMacksood/quant-portfolio-dashboard.git]
cd quant-portfolio-dashboard
```
### 2. Create a virtual environment & install dependencies
```Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```
### 3. Enable Offline Mock Data
Open ```src/data_handler.py``` and ensure the testing toggle is set to ```True```:

```Python
USE_MOCK_DATA = True
```
### 4. Run the application

```Bash
streamlit run app.py
```
## Cloud Deployment
This application is configured for continuous deployment (CI/CD) via GitHub Actions to Azure App Service.

* Azure environment variables are used to enforce the Streamlit theme (```STREAMLIT_THEME_BASE```, ```STREAMLIT_THEME_PRIMARY_COLOR```).

* Authentication to the Azure SQL Database is handled securely via Azure Managed Identity (```DefaultAzureCredential```), eliminating hardcoded connection strings.
