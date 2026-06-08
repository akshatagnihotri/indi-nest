# IndiNest — Premium Indian Housing Cost Predictor & Analytics

A machine learning-driven residential rental cost predictor and market telemetry dashboard for properties in **Delhi**, **Mumbai**, and **Pune**. Built using **scikit-learn**, **FastAPI**, and a visual interface inspired by **TruPath Ventures**.

Trained on **13,910 listings**, the regression engine predicts monthly rental costs with high accuracy, auto-resolving geo-coordinates for spatial analysis and displaying dynamic market metrics.

---

## 🛠️ Tech Stack & Architecture

- **Machine Learning Model**: Python, Scipy, Pandas, NumPy, scikit-learn (`HistGradientBoostingRegressor`)
- **Backend API Server**: FastAPI (Asynchronous Python REST API), Uvicorn, joblib
- **Frontend Dashboard**: HTML5, Vanilla CSS3 (Glassmorphism layout), ES6+ JavaScript, Lucide Icons

```
[CSV Datasets] ──> [train_model.py] ──> [model_pipeline.joblib]
                                                 │
                                                 ▼
[Web Client (UI)] <── [app.py (FastAPI)] <───────┘
```

---

## ✨ Features

### 1. High-Precision Predictions
- Takes parameters like **city**, **locality**, **property type**, **furnishing status**, **built-up area (Sq. Ft.)**, **BHK**, **bathrooms**, and **balconies**.
- Feeds inputs through a Gradient Boosting regressor with optimized categorical splits.
- Explains **92.09%** of the rental cost variance.

### 2. Spatial Coordinate Lookup Table
- Tracks **669 unique locations** across India.
- Computes the robust median latitude and longitude coordinates per locality during training.
- Auto-completes geographical coordinate values for backend predictions, removing the need for user coordinate input.

### 3. Market Telemetry Analytics
- **Live Average Rent**: Displays average rent levels per city (Delhi, Mumbai, Pune).
- **Spread Distributions**: Visual bar charts detailing BHK spreads and Furnishing value impacts.
- **Localities Hotspots**: Toggleable selectors showing the top 5 most expensive localities per city based on median rental costs.

### 4. Premium Visual Interface
- Deep graphite black theme (`#0d0d0d`) with drafting grids and brass/gold accents (`#b8892a`).
- Custom reticle drafting cursor tracking.
- Parallax 3D card tilt animation on hover.
- Dynamic input selector syncing (changing city updates localities list instantly).

---

## 📊 Model Performance Metrics

The model is evaluated on a random 15% validation split:
- **Validation R² Score**: `0.9209` (92.09% accuracy)
- **Mean Absolute Error (MAE)**: `21,858.47 INR`
- **Root Mean Squared Error (RMSE)**: `55,491.24 INR`

---

## 📁 Project Structure

```
├── static/
│   ├── index.html     # Premium glassmorphic telemetry UI
│   ├── style.css      # Core styles, grid layout, animations, cursor reticle
│   └── script.js      # Form handler, 3D card tilt logic, API dynamic hooks
├── app.py             # FastAPI backend server & predict router
├── train_model.py     # Data pipeline, cleaner, HGB regressor training
├── requirements.txt   # Python dependency list
├── README.md          # Project guide
└── *.csv              # Indian housing listings source data
```

---

## 🚀 Setup & Execution

### Prerequisite: Install dependencies
Ensure Python is installed, then run:
```bash
pip install -r requirements.txt
```

### Step 1: Train the model
Run the training script to merge the raw listing CSVs, preprocess attributes, resolve median coordinates, train the regressor, and serialize the pipeline:
```bash
python train_model.py
```
*Outputs `model_pipeline.joblib` to the root folder.*

### Step 2: Start the backend server
Run the FastAPI web server using Uvicorn:
```bash
python -m uvicorn app:app --port 8000 --host 127.0.0.1
```

### Step 3: Open the dashboard
Open your browser and navigate to:
```url
http://127.0.0.1:8000
```