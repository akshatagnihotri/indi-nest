import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np
import re
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error
import os

def clean_size(size_str):
    if pd.isna(size_str):
        return np.nan
    # Remove commas and extract numeric value
    size_str = str(size_str).replace(',', '')
    match = re.search(r'(\d+(?:\.\d+)?)', size_str)
    if match:
        return float(match.group(1))
    return np.nan

def clean_bhk(type_str):
    if pd.isna(type_str):
        return 1.0
    type_str = str(type_str).lower()
    # Match digit followed by BHK or RK or Studio
    match = re.search(r'(\d+)\s*(?:bhk|rk|studio|bedroom)', type_str)
    if match:
        return float(match.group(1))
    if 'studio' in type_str or '1rk' in type_str or '1 rk' in type_str:
        return 1.0
    return 1.0

def clean_property_type(type_str):
    if pd.isna(type_str):
        return 'Other'
    type_str = str(type_str).lower()
    if 'apartment' in type_str or 'flat' in type_str:
        return 'Apartment'
    elif 'floor' in type_str:
        return 'Independent Floor'
    elif 'house' in type_str:
        return 'Independent House'
    elif 'villa' in type_str:
        return 'Villa'
    elif 'penthouse' in type_str:
        return 'Penthouse'
    elif 'studio' in type_str or 'rk' in type_str:
        return 'Studio'
    else:
        return 'Other'

def main():
    data_dir = r"c:\Users\91909\Downloads\indian housing data set"
    files = [
        os.path.join(data_dir, "Indian_housing_Delhi_data.csv"),
        os.path.join(data_dir, "Indian_housing_Mumbai_data.csv"),
        os.path.join(data_dir, "Indian_housing_Pune_data.csv")
    ]
    
    dfs = []
    for f in files:
        if os.path.exists(f):
            print(f"Loading {f}...")
            df = pd.read_csv(f)
            # Ensure city is parsed correctly
            df['city'] = df['city'].str.strip()
            # If city is not Delhi/Mumbai/Pune, let's keep it or map based on file name
            filename = os.path.basename(f).lower()
            if 'delhi' in filename:
                df['city'] = 'Delhi'
            elif 'mumbai' in filename:
                df['city'] = 'Mumbai'
            elif 'pune' in filename:
                df['city'] = 'Pune'
            dfs.append(df)
            
    if not dfs:
        print("No files loaded. Exiting.")
        return
        
    df = pd.concat(dfs, ignore_index=True)
    print(f"Total raw rows: {df.shape[0]}")
    
    # 1. Clean Target Variable (price)
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.dropna(subset=['price'])
    df = df[df['price'] > 0]
    print(f"Rows after cleaning price: {df.shape[0]}")
    
    # 2. Parse house size
    df['size_sqft'] = df['house_size'].apply(clean_size)
    df['size_sqft'] = df['size_sqft'].fillna(df['size_sqft'].median())
    
    # 3. Parse BHK and property type
    df['bhk'] = df['house_type'].apply(clean_bhk)
    df['property_type'] = df['house_type'].apply(clean_property_type)
    
    # 4. Clean location and status
    df['location'] = df['location'].str.strip().str.title()
    df['Status'] = df['Status'].str.strip().fillna('Unfurnished')
    
    # 5. Clean latitude & longitude coordinates using median mapping per city-location
    # This filters out coordinate outliers (like GPS coordinates pointing to other states)
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Calculate robust median coordinates per location
    loc_coords = df.groupby(['city', 'location'])[['latitude', 'longitude']].median().reset_index()
    
    # Compute median coordinate per city for backup fallback
    city_coords = df.groupby('city')[['latitude', 'longitude']].median().to_dict(orient='index')
    
    # Create location lookup dictionary
    location_coords_dict = {}
    for _, row in loc_coords.iterrows():
        key = (row['city'], row['location'])
        # If median coordinates are missing for the location, fallback to city level
        lat = row['latitude'] if not pd.isna(row['latitude']) else city_coords[row['city']]['latitude']
        lon = row['longitude'] if not pd.isna(row['longitude']) else city_coords[row['city']]['longitude']
        location_coords_dict[key] = {'latitude': lat, 'longitude': lon}
        
    # Map cleaned coordinates back to dataframe to replace outliers/nulls
    def clean_coords(row):
        key = (row['city'], row['location'])
        if key in location_coords_dict:
            return pd.Series([location_coords_dict[key]['latitude'], location_coords_dict[key]['longitude']])
        else:
            fallback = city_coords.get(row['city'], {'latitude': 20.0, 'longitude': 75.0})
            return pd.Series([fallback['latitude'], fallback['longitude']])
            
    df[['latitude', 'longitude']] = df.apply(clean_coords, axis=1)
    
    # 6. Parse numeric Bathrooms & Balconies
    df['numBathrooms'] = pd.to_numeric(df['numBathrooms'], errors='coerce')
    # Fill missing bathrooms: at least 1, otherwise matching BHK
    df['numBathrooms'] = df['numBathrooms'].fillna(df['bhk']).clip(lower=1)
    
    df['numBalconies'] = pd.to_numeric(df['numBalconies'], errors='coerce').fillna(0)
    
    # Calculate statistics for visual data analysis
    # Average rent by city
    avg_rent_by_city = df.groupby('city')['price'].mean().round(0).to_dict()
    # Average rent by furnishing status
    avg_rent_by_status = df.groupby('Status')['price'].mean().round(0).to_dict()
    # BHK distribution percentages
    bhk_counts = df['bhk'].value_counts()
    total_bhk = bhk_counts.sum()
    bhk_dist = {str(int(k)) if k.is_integer() else str(k): round((v / total_bhk) * 100, 1) for k, v in bhk_counts.items()}
    
    # Top 5 expensive localities per city (with count >= 5 to filter noise)
    loc_counts = df.groupby(['city', 'location']).size()
    valid_locs = loc_counts[loc_counts >= 5].index
    filtered_df = df[df.set_index(['city', 'location']).index.isin(valid_locs)]
    
    top_expensive = {}
    for city_name in ['Delhi', 'Mumbai', 'Pune']:
        city_locs = filtered_df[filtered_df['city'] == city_name]
        top_5 = city_locs.groupby('location')['price'].median().sort_values(ascending=False).head(5)
        top_expensive[city_name] = [{"location": loc, "rent": round(float(price), 0)} for loc, price in top_5.items()]

    # Features list
    features = ['city', 'location', 'property_type', 'size_sqft', 'bhk', 'numBathrooms', 'numBalconies', 'Status', 'latitude', 'longitude']
    target = 'price'
    
    X = df[features]
    y = df[target]
    
    # Save the lookup metadata dictionary for backend coordinate auto-resolution
    # Convert keys to strings so they are easily JSON-serializable, or just pickle with joblib
    lookup_metadata = {
        'location_coords': location_coords_dict,
        'city_coords': city_coords,
        # Unique locations per city for the dropdown
        'locations_by_city': df.groupby('city')['location'].unique().apply(sorted).to_dict(),
        'analysis': {
            'avg_rent_by_city': avg_rent_by_city,
            'avg_rent_by_status': avg_rent_by_status,
            'bhk_dist': bhk_dist,
            'expensive_localities': top_expensive
        }
    }
    
    # Encode categorical columns
    categorical_cols = ['city', 'location', 'property_type', 'Status']
    
    # Train test split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.15, random_state=42)
    
    print("\nTraining HistGradientBoostingRegressor model...")
    
    # Use OrdinalEncoder to encode categories for HistGradientBoostingRegressor
    # It natively supports categorical features if we tell it which columns are categorical
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    
    X_train_encoded = X_train.copy()
    X_val_encoded = X_val.copy()
    
    X_train_encoded[categorical_cols] = encoder.fit_transform(X_train[categorical_cols])
    X_val_encoded[categorical_cols] = encoder.transform(X_val[categorical_cols])
    
    # HistGradientBoostingRegressor only supports categorical features with cardinality <= 255.
    # Since 'location' has 600+ unique values, we pass only 'city', 'property_type', and 'Status' as categorical,
    # and treat 'location' as a standard numerical feature (its values are already mapped to ordinals).
    model_categorical_cols = ['city', 'property_type', 'Status']
    categorical_features_indices = [features.index(col) for col in model_categorical_cols]
    
    model = HistGradientBoostingRegressor(
        categorical_features=categorical_features_indices,
        random_state=42,
        max_iter=250,
        learning_rate=0.08,
        max_depth=8
    )
    
    model.fit(X_train_encoded, y_train)
    
    # Predict
    val_preds = model.predict(X_val_encoded)
    
    # Metrics
    r2 = r2_score(y_val, val_preds)
    mae = mean_absolute_error(y_val, val_preds)
    rmse = root_mean_squared_error(y_val, val_preds)
    
    print(f"Validation R^2 Score: {r2:.4f}")
    print(f"Validation MAE: {mae:.2f} INR")
    print(f"Validation RMSE: {rmse:.2f} INR")
    
    # Export full pipeline
    pipeline = {
        'model': model,
        'encoder': encoder,
        'features': features,
        'categorical_cols': categorical_cols,
        'metadata': lookup_metadata
    }
    
    output_path = os.path.join(data_dir, "model_pipeline.joblib")
    joblib.dump(pipeline, output_path)
    print(f"Saved model pipeline to: {output_path}")

if __name__ == "__main__":
    main()
