from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import pickle
from typing import Literal, Optional
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import requests

app = FastAPI(
    title="Delivery Time Prediction API",
    description="ML-powered API with cooking + delivery time breakdown",
    version="2.0.0"
)

# Load model artifact
try:
    with open("model/dtmodel.pkl", "rb") as f:
        artifact = pickle.load(f)
    model = artifact["model"]
    encoder = artifact["encoder"]
    feature_columns = artifact["feature_columns"]
    print(f"✅ Model loaded successfully!")
    print(f"📊 Features: {len(feature_columns)}")
    print(f"Feature list: {feature_columns}")
except Exception as e:
    raise RuntimeError(f"❌ Failed to load model artifact: {e}")


# ============ HELPER FUNCTIONS ============

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return round(distance, 2)


def geocode_address(address: str, api_key: str):
    """Convert address to lat/long using OpenCage"""
    try:
        url = f"https://api.opencagedata.com/geocode/v1/json"
        params = {"q": address, "key": api_key, "limit": 1}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                return {
                    "latitude": data["results"][0]["geometry"]["lat"],
                    "longitude": data["results"][0]["geometry"]["lng"]
                }
        return None
    except Exception as e:
        raise HTTPException(500, f"Geocoding error: {str(e)}")


# ============ REQUEST MODELS ============

class DeliveryRequest(BaseModel):
    """Complete delivery prediction request with time features"""
    
    # Location coordinates
    restaurant_latitude: float = Field(..., ge=-90, le=90, example=22.745049)
    restaurant_longitude: float = Field(..., ge=-180, le=180, example=75.892471)
    delivery_latitude: float = Field(..., ge=-90, le=90, example=22.765049)
    delivery_longitude: float = Field(..., ge=-180, le=180, example=75.912471)
    
    # Delivery partner info
    delivery_person_age: float = Field(..., ge=18, le=65, example=28)
    delivery_person_ratings: float = Field(..., ge=1.0, le=5.0, example=4.5)
    
    # Order context
    weather_conditions: Literal["Sunny", "Stormy", "Cloudy", "Fog", "Sandstorms", "Windy"]
    road_traffic_density: Literal["Low", "Medium", "High", "Jam"]
    type_of_order: Literal["Snack", "Meal", "Drinks", "Buffet"]
    type_of_vehicle: Literal["motorcycle", "scooter", "electric_scooter"]
    city: Literal["Urban", "Semi-Urban", "Metropolitian"]
    festival: Literal["Yes", "No"] = "No"
    
    # Time features (from Streamlit)
    day: int = Field(..., ge=1, le=31, example=15)
    month: int = Field(..., ge=1, le=12, example=12)
    day_of_week: int = Field(..., ge=0, le=6, example=3)
    is_weekend: int = Field(..., ge=0, le=1, example=0)
    hour: int = Field(..., ge=0, le=23, example=18)
    is_rush_hour: int = Field(..., ge=0, le=1, example=1)
    
    # Optional with defaults
    vehicle_condition: int = Field(2, ge=0, le=3, example=2)
    multiple_deliveries: int = Field(0, ge=0, le=4, example=0)
    order_prepare_time: float = Field(15.0, ge=0, le=180, example=15.0)
    city_code: str = Field("INDO", min_length=3, max_length=4, example="INDO")


class AddressBasedRequest(BaseModel):
    """Address-based prediction request"""
    
    # Addresses
    restaurant_address: str = Field(..., example="Vatika Business Park, Sector 49, Gurgaon")
    delivery_address: str = Field(..., example="DLF Cyber City, Gurgaon")
    opencage_api_key: str = Field(..., description="OpenCage API key for geocoding")
    
    # Delivery partner
    delivery_person_age: float = Field(28, ge=18, le=65)
    delivery_person_ratings: float = Field(4.5, ge=1.0, le=5.0)
    
    # Order context
    weather_conditions: Literal["Sunny", "Stormy", "Cloudy", "Fog", "Sandstorms", "Windy"] = "Sunny"
    road_traffic_density: Literal["Low", "Medium", "High", "Jam"] = "Medium"
    type_of_order: Literal["Snack", "Meal", "Drinks", "Buffet"] = "Meal"
    type_of_vehicle: Literal["motorcycle", "scooter", "electric_scooter"] = "motorcycle"
    city: Literal["Urban", "Semi-Urban", "Metropolitian"] = "Urban"
    festival: Literal["Yes", "No"] = "No"
    
    # Time features
    day: int = Field(..., ge=1, le=31)
    month: int = Field(..., ge=1, le=12)
    day_of_week: int = Field(..., ge=0, le=6)
    is_weekend: int = Field(..., ge=0, le=1)
    hour: int = Field(..., ge=0, le=23)
    is_rush_hour: int = Field(..., ge=0, le=1)
    
    # Optional
    vehicle_condition: int = Field(2, ge=0, le=3)
    multiple_deliveries: int = Field(0, ge=0, le=4)
    order_prepare_time: float = Field(15.0, ge=0, le=180)
    city_code: str = Field("INDO", min_length=3, max_length=4)


# ============ PREDICTION LOGIC ============

def prepare_features_for_prediction(data: dict, distance: float) -> pd.DataFrame:
    """
    Prepare all features including derived ones for prediction
    """
    # Calculate avg_speed_kmh (derived feature from training)
    # Estimate delivery time component (total - prep time) to calculate speed
    estimated_delivery_time = max(data["order_prepare_time"] * 0.6, 10)  # Rough estimate
    avg_speed_kmh = (distance / estimated_delivery_time) * 60 if estimated_delivery_time > 0 else 20
    
    # Build complete feature dictionary matching training data
    features = {
        "Delivery_person_Age": data["delivery_person_age"],
        "Delivery_person_Ratings": data["delivery_person_ratings"],
        "Restaurant_latitude": data["restaurant_latitude"],
        "Restaurant_longitude": data["restaurant_longitude"],
        "Delivery_location_latitude": data["delivery_latitude"],
        "Delivery_location_longitude": data["delivery_longitude"],
        "Weather_conditions": data["weather_conditions"],
        "Road_traffic_density": data["road_traffic_density"],
        "Vehicle_condition": data["vehicle_condition"],
        "Type_of_order": data["type_of_order"],
        "Type_of_vehicle": data["type_of_vehicle"],
        "multiple_deliveries": data["multiple_deliveries"],
        "Festival": data["festival"],
        "City": data["city"],
        "City_code": data["city_code"],
        "order_prepare_time": data["order_prepare_time"],
        "distance": distance,
        "day": data["day"],
        "month": data["month"],
        "day_of_week": data["day_of_week"],
        "is_weekend": data["is_weekend"],
        "hour": data["hour"],
        "is_rush_hour": data["is_rush_hour"],
        "avg_speed_kmh": avg_speed_kmh
    }
    
    # Convert to DataFrame
    input_df = pd.DataFrame([features])
    
    # Encode categorical columns
    cat_cols = encoder.feature_names_in_
    input_df[cat_cols] = encoder.transform(input_df[cat_cols])
    
    # Ensure all features are present and in correct order
    for col in feature_columns:
        if col not in input_df.columns:
            input_df[col] = 0
    
    # Reorder to match training
    input_df = input_df[feature_columns]
    
    return input_df


# ============ API ENDPOINTS ============

@app.get("/", tags=["Health"])
def health_check():
    """API health check"""
    return {
        "status": "running",
        "version": "2.0.0",
        "model_loaded": True,
        "features_count": len(feature_columns),
        "message": "Delivery Time Prediction API with cooking + delivery breakdown"
    }


@app.get("/health", tags=["Health"])
def detailed_health():
    """Detailed health information"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "encoder_loaded": encoder is not None,
        "feature_count": len(feature_columns),
        "expected_features": feature_columns
    }


@app.post("/predict", tags=["Prediction"])
def predict_delivery_time(request: DeliveryRequest):
    """
    Predict delivery time using coordinates
    Returns total time = cooking time + delivery time
    """
    
    try:
        # Calculate distance
        distance = calculate_distance(
            request.restaurant_latitude,
            request.restaurant_longitude,
            request.delivery_latitude,
            request.delivery_longitude
        )
        
        # Validate distance
        if distance > 100:
            raise HTTPException(
                status_code=400,
                detail=f"Distance too large ({distance:.2f} km). Maximum 100km for delivery."
            )
        
        if distance <= 0:
            raise HTTPException(status_code=400, detail="Invalid coordinates - distance is zero")
        
        # Prepare request data
        data = {
            "restaurant_latitude": request.restaurant_latitude,
            "restaurant_longitude": request.restaurant_longitude,
            "delivery_latitude": request.delivery_latitude,
            "delivery_longitude": request.delivery_longitude,
            "delivery_person_age": request.delivery_person_age,
            "delivery_person_ratings": request.delivery_person_ratings,
            "weather_conditions": request.weather_conditions,
            "road_traffic_density": request.road_traffic_density,
            "type_of_order": request.type_of_order,
            "type_of_vehicle": request.type_of_vehicle,
            "city": request.city,
            "festival": request.festival,
            "vehicle_condition": request.vehicle_condition,
            "multiple_deliveries": request.multiple_deliveries,
            "order_prepare_time": request.order_prepare_time,
            "city_code": request.city_code,
            "day": request.day,
            "month": request.month,
            "day_of_week": request.day_of_week,
            "is_weekend": request.is_weekend,
            "hour": request.hour,
            "is_rush_hour": request.is_rush_hour
        }
        
        # Prepare features
        input_df = prepare_features_for_prediction(data, distance)
        
        # Make prediction (model was trained without log transform in improved version)
        prediction = model.predict(input_df)[0]
        
        # Clip to reasonable range (5-120 minutes)
        predicted_time = float(np.clip(prediction, 5, 120))
        
        # Calculate breakdown
        prep_time = request.order_prepare_time
        # estimated_delivery_time = max(predicted_time - prep_time, 5) + 20
        estimated_delivery_time = predicted_time + prep_time
        avg_speed = (distance / estimated_delivery_time) * 60 if estimated_delivery_time > 0 else 0
        
        return {
            "success": True,
            "predicted_delivery_time_minutes": round(predicted_time + 20, 2),
            "calculated_distance_km": distance,
            "breakdown": {
                "preparation_time_minutes": round(prep_time, 2),
                "estimated_delivery_time_minutes": round(estimated_delivery_time, 2),
                "average_speed_kmh": round(avg_speed, 2)
            },
            "conditions": {
                "weather": request.weather_conditions,
                "traffic": request.road_traffic_density,
                "is_rush_hour": bool(request.is_rush_hour),
                "is_weekend": bool(request.is_weekend),
                "festival": request.festival,
                "order_type": request.type_of_order
            },
            "order_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict-with-address", tags=["Prediction"])
def predict_with_addresses(request: AddressBasedRequest):
    """
    Predict delivery time using addresses instead of coordinates
    """
    
    try:
        # Geocode restaurant address
        rest_coords = geocode_address(request.restaurant_address, request.opencage_api_key)
        if not rest_coords:
            raise HTTPException(400, "Failed to geocode restaurant address")
        
        # Geocode delivery address
        del_coords = geocode_address(request.delivery_address, request.opencage_api_key)
        if not del_coords:
            raise HTTPException(400, "Failed to geocode delivery address")
        
        # Create coordinate-based request
        coord_request = DeliveryRequest(
            restaurant_latitude=rest_coords["latitude"],
            restaurant_longitude=rest_coords["longitude"],
            delivery_latitude=del_coords["latitude"],
            delivery_longitude=del_coords["longitude"],
            delivery_person_age=request.delivery_person_age,
            delivery_person_ratings=request.delivery_person_ratings,
            weather_conditions=request.weather_conditions,
            road_traffic_density=request.road_traffic_density,
            type_of_order=request.type_of_order,
            type_of_vehicle=request.type_of_vehicle,
            city=request.city,
            festival=request.festival,
            vehicle_condition=request.vehicle_condition,
            multiple_deliveries=request.multiple_deliveries,
            order_prepare_time=request.order_prepare_time,
            city_code=request.city_code,
            day=request.day,
            month=request.month,
            day_of_week=request.day_of_week,
            is_weekend=request.is_weekend,
            hour=request.hour,
            is_rush_hour=request.is_rush_hour
        )
        
        # Use existing prediction endpoint
        result = predict_delivery_time(coord_request)
        
        # Add geocoded coordinates to response
        result["geocoded_coordinates"] = {
            "restaurant": rest_coords,
            "delivery": del_coords
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Address-based prediction failed: {str(e)}")


@app.post("/geocode", tags=["Utilities"])
def geocode_endpoint(address: str, api_key: str):
    """Utility endpoint to convert address to coordinates"""
    
    result = geocode_address(address, api_key)
    if result:
        return result
    else:
        raise HTTPException(400, "Geocoding failed - check address and API key")


# CORS middleware for frontend integration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)