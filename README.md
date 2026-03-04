# Auto-Viz

**Instant Data Visualization from Raw Data**

Auto-Viz is a web application that automatically generates intelligent visualizations from your CSV and Excel files. No manual chart configuration required - just upload your data and get instant, meaningful visualizations.

## How It Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (AngularJS)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Dashboard   │  │   Upload     │  │   Groups     │           │
│  │    View      │  │    Zone      │  │    View      │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                           │                                       │
│                    File Upload (CSV/Excel)                        │
└───────────────────────────┼───────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Flask API)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Data Analysis Engine                    │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │   │
│  │  │  Column    │  │   Type     │  │   Visualization    │  │   │
│  │  │  Analyzer  │  │  Detector  │  │   Recommender      │  │   │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                       │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Chart Data Generator                       │   │
│  │  Transforms raw data → Chart.js compatible format          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Storage                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   uploads/   │  │   data/      │  │   JSON DB    │           │
│  │  Raw files   │  │ dashboards   │  │  Persistence │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Core Concepts

#### 1. Smart Column Analysis

When you upload a file, Auto-Viz analyzes each column to understand its characteristics:

```python
Column Types Detected:
├── continuous      → Numeric with many unique values (sales, prices)
├── categorical_numeric → Numeric with few unique values (ratings 1-5)
├── categorical     → Text with repeating values (regions, categories)
├── datetime        → Date/time values (timestamps, dates)
└── text            → High cardinality text (descriptions, names)
```

**Detection Logic:**
- **Numeric columns**: If unique values ≤ 10, treat as categorical; otherwise continuous
- **DateTime**: Attempts to parse as date; if successful, marks as datetime
- **Categorical**: Text columns where unique/total ratio < 5% or unique ≤ 20
- **Text**: High cardinality text (names, descriptions) - not visualized

#### 2. Visualization Recommendation Engine

Based on column analysis, the system recommends appropriate chart types:

| Data Pattern | Recommended Chart | Priority |
|--------------|-------------------|----------|
| Single numeric distribution | Histogram | 1 |
| Categorical value counts | Bar Chart | 2 |
| Category breakdown | Pie Chart | 3 |
| Time + Numeric | Line Chart | 1 |
| Numeric vs Numeric | Scatter Plot | 2 |
| Category + Numeric | Grouped Bar | 2 |

**Recommendation Rules:**
```
IF numeric column exists:
    → Generate histogram for distribution analysis

IF categorical column with ≤15 unique values:
    → Generate bar chart for counts
    → Generate pie chart for proportions

IF datetime column + numeric column:
    → Generate line chart for time series

IF 2+ numeric columns:
    → Generate scatter plot for correlation

IF categorical + numeric:
    → Generate grouped bar for comparison
```

#### 3. Chart Data Transformation

Raw data is transformed into Chart.js compatible format:

```javascript
// Example: Bar Chart Data
{
  "labels": ["Electronics", "Furniture", "Clothing"],
  "datasets": [{
    "label": "Count",
    "data": [150, 89, 67],
    "backgroundColor": "rgba(0, 255, 136, 0.6)",
    "borderColor": "rgba(0, 255, 136, 1)"
  }]
}

// Example: Scatter Plot Data
{
  "datasets": [{
    "data": [
      {"x": 100, "y": 4.5},
      {"x": 200, "y": 4.2},
      {"x": 150, "y": 4.8}
    ]
  }]
}
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve the main application |
| `/api/upload` | POST | Upload file and generate visualizations |
| `/api/dashboards` | GET | List all dashboards |
| `/api/dashboards/<id>` | GET | Get single dashboard |
| `/api/dashboards/<id>` | DELETE | Delete dashboard |
| `/api/groups` | GET/POST | List or create groups |
| `/api/groups/<id>` | PUT/DELETE | Update or delete group |

### Data Flow

```
1. USER UPLOADS FILE
   └── File saved to /uploads/

2. DATA PARSING
   ├── CSV → pandas.read_csv()
   └── Excel → pandas.read_excel()

3. COLUMN ANALYSIS
   ├── Detect data types
   ├── Count unique values
   ├── Check null percentages
   └── Classify column purpose

4. VISUALIZATION RECOMMENDATION
   ├── Match column types to chart types
   ├── Score recommendations by priority
   └── Select top 12 visualizations

5. CHART DATA GENERATION
   ├── Transform data for each chart type
   ├── Apply sampling for large datasets
   └── Format for Chart.js

6. DASHBOARD CREATION
   ├── Store dashboard metadata
   ├── Save chart configurations
   └── Persist to JSON storage

7. FRONTEND RENDERING
   ├── Receive dashboard data
   ├── Render Chart.js visualizations
   └── Display in responsive grid
```

## Installation & Setup

### Requirements
- Python 3.8+
- Modern web browser

### Install Dependencies
```bash
cd /root/auto-viz
pip install -r requirements.txt
```

### Run Application
```bash
python app.py
```

The app will be available at: `http://localhost:5002`

## Features

### Dashboard View
- Grid of all created dashboards
- Shows chart count, row count, column count
- Click to view full visualization
- Delete dashboards

### Upload Zone
- Drag & drop file upload
- Supports CSV, XLSX, XLS
- Real-time progress indicator
- Instant visualization generation

### Groups
- Organize dashboards into groups
- Create/delete groups
- Select multiple dashboards per group

### Chart Types Generated
- **Histogram**: Distribution of numeric values
- **Bar Chart**: Category frequencies
- **Pie Chart**: Proportional breakdown
- **Line Chart**: Time series trends
- **Scatter Plot**: Correlation between numerics
- **Grouped Bar**: Category comparisons

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask (Python) |
| Frontend | AngularJS 1.8 |
| Charts | Chart.js 4.x |
| Data Processing | Pandas, NumPy |
| Styling | Custom CSS (Dark Theme) |
| Icons | Font Awesome |

## File Structure

```
/root/auto-viz/
├── app.py              # Flask application & API
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── sample_data.csv    # Sample test data
├── static/
│   ├── index.html     # Main HTML template
│   ├── css/
│   │   └── style.css  # Dark theme styles
│   └── js/
│       └── app.js     # AngularJS application
├── uploads/           # Uploaded files (created on first upload)
└── data/              # Persistent storage (created on first save)
    ├── dashboards.json
    └── groups.json
```

## Theme

The application uses a dark theme with green accents:
- **Background**: #0a0a0f (primary), #12121a (secondary)
- **Accent**: #00ff88 (neon green)
- **Cards**: #16161f with #2a2a3e borders
- **Glow effects** on buttons and interactive elements
