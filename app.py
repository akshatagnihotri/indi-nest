import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Indian Housing Cost Predictor")

# Load model pipeline
pipeline_path = os.path.join(os.path.dirname(__file__), "model_pipeline.joblib")

# Global variables for pipeline components
model = None
encoder = None
features = None
categorical_cols = None
metadata = None

def load_pipeline():
    global model, encoder, features, categorical_cols, metadata
    if not os.path.exists(pipeline_path):
        raise RuntimeError(f"Model pipeline not found at {pipeline_path}. Please train the model first.")
    
    print("Loading model pipeline...")
    pipeline = joblib.load(pipeline_path)
    model = pipeline['model']
    encoder = pipeline['encoder']
    features = pipeline['features']
    categorical_cols = pipeline['categorical_cols']
    metadata = pipeline['metadata']
    print("Model pipeline loaded successfully.")

# Load pipeline on startup
@app.on_event("startup")
def startup_event():
    load_pipeline()

class PredictionRequest(BaseModel):
    city: str
    location: str
    property_type: str
    size_sqft: float
    bhk: float
    numBathrooms: float
    numBalconies: float
    Status: str

@app.post("/predict")
def predict(req: PredictionRequest):
    if model is None:
        load_pipeline()
        
    city_key = req.city.strip()
    loc_key = req.location.strip().title()
    
    location_coords = metadata['location_coords']
    city_coords = metadata['city_coords']
    
    # Resolve coordinates for the (city, location)
    key = (city_key, loc_key)
    if key in location_coords:
        lat = location_coords[key]['latitude']
        lon = location_coords[key]['longitude']
    else:
        # fallback to city coordinates
        if city_key in city_coords:
            lat = city_coords[city_key]['latitude']
            lon = city_coords[city_key]['longitude']
        else:
            lat = 20.0
            lon = 75.0
            
    # Construct dataframe row
    data_dict = {
        'city': [city_key],
        'location': [loc_key],
        'property_type': [req.property_type],
        'size_sqft': [req.size_sqft],
        'bhk': [req.bhk],
        'numBathrooms': [req.numBathrooms],
        'numBalconies': [req.numBalconies],
        'Status': [req.Status],
        'latitude': [lat],
        'longitude': [lon]
    }
    
    df_pred = pd.DataFrame(data_dict)[features]
    
    # Encode categoricals
    try:
        df_pred_encoded = df_pred.copy()
        df_pred_encoded[categorical_cols] = encoder.transform(df_pred[categorical_cols])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Data encoding error: {str(e)}")
        
    # Run prediction
    try:
        predicted_val = model.predict(df_pred_encoded)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction engine error: {str(e)}")
        
    return {
        "predicted_price": round(float(predicted_val), 2),
        "latitude": lat,
        "longitude": lon,
        "location": loc_key,
        "city": city_key
    }

@app.get("/api/locations")
def get_locations(city: str):
    if metadata is None:
        load_pipeline()
    city_key = city.strip()
    locations_by_city = metadata['locations_by_city']
    if city_key in locations_by_city:
        return {"locations": locations_by_city[city_key]}
    return {"locations": []}

@app.get("/api/cities")
def get_cities():
    if metadata is None:
        load_pipeline()
    locations_by_city = metadata['locations_by_city']
    return {"cities": list(locations_by_city.keys())}

@app.get("/api/analysis")
def get_analysis():
    if metadata is None:
        load_pipeline()
    return metadata.get('analysis', {})

# Mount static web assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
