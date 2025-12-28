import streamlit as st
import requests
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="🚚 Smart Delivery Time Predictor",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    .prediction-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    .prediction-time {
        font-size: 4rem;
        font-weight: bold;
        margin: 1rem 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .time-breakdown {
        display: flex;
        justify-content: space-around;
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 2px solid rgba(255,255,255,0.3);
    }
    .time-component {
        text-align: center;
    }
    .time-component-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .time-component-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    .info-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #667eea;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.3rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-size: 1.2rem;
        padding: 0.8rem;
        border-radius: 12px;
        border: none;
        font-weight: bold;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    .feature-badge {
        display: inline-block;
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem;
        font-weight: 500;
    }
    .warning-box {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🚚 Smart Delivery Time Predictor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered ETA with Cooking + Delivery Time Analysis</div>', unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Configuration
    st.subheader("🔌 API Settings")
    api_base_url = st.text_input(
        "FastAPI Base URL",
        value="http://localhost:8000",
        help="Your FastAPI server URL"
    )
    
    opencage_api_key = st.text_input(
        "OpenCage API Key (Optional)",
        type="password",
        help="For address-based geocoding"
    )
    
    st.divider()
    
    # Input Mode
    st.subheader("📍 Input Mode")
    input_mode = st.radio(
        "Choose input method:",
        ["📍 Coordinates", "🏠 Addresses"],
        help="Use coordinates for faster predictions"
    )
    
    st.divider()
    
    # Quick Presets
    st.subheader("🎯 Quick Presets")
    preset = st.selectbox(
        "Load Scenario",
        ["None", "Rush Hour (High Traffic)", "Late Night (Low Traffic)", 
         "Weekend Festival", "Rainy Day", "Long Distance"]
    )
    
    st.divider()
    
    # Model Info
    with st.expander("ℹ️ About This Model"):
        st.markdown("""
        **Features:**
        - 🧠 XGBoost ML Model
        - 🍳 Cooking Time Analysis
        - 🚗 Delivery Time Prediction
        - 📊 Distance-based Optimization
        - 🌦️ Weather Impact
        - 🚦 Traffic Conditions
        - ⏰ Rush Hour Detection
        
        **Total ETA = Prep Time + Delivery Time**
        """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📋 Order Details")
    
    # Location Input based on mode
    if input_mode == "🏠 Addresses":
        st.subheader("📍 Locations")
        restaurant_address = st.text_input(
            "🏪 Restaurant Address",
            value="Vatika Business Park, Sector 49, Gurgaon",
            help="Enter the restaurant's full address"
        )
        delivery_address = st.text_input(
            "🏠 Delivery Address",
            value="DLF Cyber City, Gurgaon",
            help="Enter the delivery destination address"
        )
        
        if not opencage_api_key:
            st.warning("⚠️ Please add OpenCage API key in sidebar for address-based input")
    
    else:  # Coordinates mode
        st.subheader("📍 Restaurant Location")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            restaurant_lat = st.number_input("Latitude", value=22.745049, format="%.6f", key="rest_lat")
        with col_r2:
            restaurant_lon = st.number_input("Longitude", value=75.892471, format="%.6f", key="rest_lon")
        
        st.subheader("📍 Delivery Location")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            delivery_lat = st.number_input("Latitude", value=22.765049, format="%.6f", key="del_lat")
        with col_d2:
            delivery_lon = st.number_input("Longitude", value=75.912471, format="%.6f", key="del_lon")
    
    st.divider()
    
    # Delivery Partner Details
    st.subheader("👤 Delivery Partner")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        delivery_age = st.slider("Age", 18, 65, 28, help="Delivery person's age")
    with col_p2:
        delivery_rating = st.slider("Rating", 1.0, 5.0, 4.5, 0.1, help="Partner's average rating")
    
    st.divider()
    
    # Order Context
    st.subheader("🍔 Order Information")
    col_o1, col_o2 = st.columns(2)
    with col_o1:
        order_type = st.selectbox("Order Type", ["Meal", "Snack", "Drinks", "Buffet"],
                                  help="Affects preparation time")
        vehicle_type = st.selectbox("Vehicle", ["motorcycle", "scooter", "electric_scooter"],
                                   help="Affects delivery speed")
    with col_o2:
        city_type = st.selectbox("City Type", ["Urban", "Semi-Urban", "Metropolitian"],
                                help="City classification")
        festival = st.selectbox("Festival Day?", ["No", "Yes"],
                               help="Festivals increase preparation and delivery time")
    
    st.divider()
    
    # Conditions
    st.subheader("🌦️ Current Conditions")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        weather = st.selectbox("Weather", ["Sunny", "Cloudy", "Fog", "Windy", "Stormy", "Sandstorms"],
                              help="Weather affects delivery time")
    with col_c2:
        traffic = st.selectbox("Traffic", ["Low", "Medium", "High", "Jam"],
                              help="Traffic density affects delivery speed")
    with col_c3:
        vehicle_condition = st.slider("Vehicle Condition", 0, 3, 2,
                                     help="0=Poor, 3=Excellent")
    
    st.divider()
    
    # Time Settings
    st.subheader("⏰ Time Settings")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        order_date = st.date_input("Order Date", datetime.now())
        order_time = st.time_input("Order Time", datetime.now().time())
    with col_t2:
        # Calculate derived features
        day_of_week = order_date.weekday()
        is_weekend = "Yes" if day_of_week >= 5 else "No"
        is_rush_hour = "Yes" if order_time.hour in [8,9,10,17,18,19,20] else "No"
        
        st.info(f"📅 Day: {order_date.strftime('%A')}")
        st.info(f"🎉 Weekend: {is_weekend}")
        st.info(f"🚦 Rush Hour: {is_rush_hour}")
    
    st.divider()
    
    # Advanced Options
    with st.expander("🔧 Advanced Options"):
        col_a1, col_a2, col_a3 = st.columns(3)
        with col_a1:
            prep_time = st.number_input("Prep Time (min)", 0.0, 180.0, 15.0,
                                       help="Estimated cooking/packing time")
        with col_a2:
            multiple_deliveries = st.number_input("Multiple Deliveries", 0, 4, 0,
                                                 help="Number of other deliveries in queue")
        with col_a3:
            city_code = st.text_input("City Code", "INDO", max_chars=4)

with col2:
    st.header("🎯 Prediction Results")
    
    # Apply Presets
    if preset != "None":
        st.info(f"📦 **Preset:** {preset}")
        if preset == "Rush Hour (High Traffic)":
            weather = "Sunny"
            traffic = "Jam"
            city_type = "Metropolitian"
            festival = "No"
            order_time = datetime.strptime("18:30", "%H:%M").time()
        elif preset == "Late Night (Low Traffic)":
            weather = "Cloudy"
            traffic = "Low"
            city_type = "Semi-Urban"
            festival = "No"
            order_time = datetime.strptime("23:00", "%H:%M").time()
        elif preset == "Weekend Festival":
            weather = "Sunny"
            traffic = "High"
            city_type = "Urban"
            festival = "Yes"
            order_date = datetime.now().replace(day=datetime.now().day + (5-datetime.now().weekday()))
        elif preset == "Rainy Day":
            weather = "Stormy"
            traffic = "High"
            city_type = "Urban"
            festival = "No"
        elif preset == "Long Distance":
            delivery_lat = restaurant_lat + 0.5
            delivery_lon = restaurant_lon + 0.5
            traffic = "Medium"
    
    # Predict Button
    if st.button("🚀 Predict Delivery Time", use_container_width=True):
        with st.spinner("🔮 Analyzing delivery factors..."):
            try:
                # Calculate derived features
                day = order_date.day
                month = order_date.month
                day_of_week = order_date.weekday()
                is_weekend_int = 1 if day_of_week >= 5 else 0
                hour = order_time.hour
                is_rush_hour_int = 1 if hour in [8,9,10,17,18,19,20] else 0
                
                # Prepare request based on input mode
                if input_mode == "🏠 Addresses":
                    if not opencage_api_key:
                        st.error("❌ OpenCage API key required for address-based input!")
                        st.stop()
                    
                    payload = {
                        "restaurant_address": restaurant_address,
                        "delivery_address": delivery_address,
                        "opencage_api_key": opencage_api_key,
                        "delivery_person_age": delivery_age,
                        "delivery_person_ratings": delivery_rating,
                        "weather_conditions": weather,
                        "road_traffic_density": traffic,
                        "type_of_order": order_type,
                        "type_of_vehicle": vehicle_type,
                        "city": city_type,
                        "festival": festival,
                        "vehicle_condition": vehicle_condition,
                        "multiple_deliveries": multiple_deliveries,
                        "order_prepare_time": prep_time,
                        "city_code": city_code,
                        "day": day,
                        "month": month,
                        "day_of_week": day_of_week,
                        "is_weekend": is_weekend_int,
                        "hour": hour,
                        "is_rush_hour": is_rush_hour_int
                    }
                    
                    response = requests.post(
                        f"{api_base_url}/predict-with-address",
                        json=payload,
                        timeout=10
                    )
                
                else:  # Coordinates mode
                    payload = {
                        "restaurant_latitude": restaurant_lat,
                        "restaurant_longitude": restaurant_lon,
                        "delivery_latitude": delivery_lat,
                        "delivery_longitude": delivery_lon,
                        "delivery_person_age": delivery_age,
                        "delivery_person_ratings": delivery_rating,
                        "weather_conditions": weather,
                        "road_traffic_density": traffic,
                        "type_of_order": order_type,
                        "type_of_vehicle": vehicle_type,
                        "city": city_type,
                        "festival": festival,
                        "vehicle_condition": vehicle_condition,
                        "multiple_deliveries": multiple_deliveries,
                        "order_prepare_time": prep_time,
                        "city_code": city_code,
                        "day": day,
                        "month": month,
                        "day_of_week": day_of_week,
                        "is_weekend": is_weekend_int,
                        "hour": hour,
                        "is_rush_hour": is_rush_hour_int
                    }
                    
                    response = requests.post(
                        f"{api_base_url}/predict",
                        json=payload,
                        timeout=10
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    predicted_time = result["predicted_delivery_time_minutes"]
                    
                    # Calculate estimated delivery time (excluding prep)
                    estimated_delivery = predicted_time - prep_time
                    
                    # Display main prediction
                    st.markdown(f"""
                        <div class="prediction-box">
                            <div style="font-size: 1.3rem; opacity: 0.95;">🕐 Total Estimated Time</div>
                            <div class="prediction-time">{predicted_time:.0f} min</div>
                            <div style="font-size: 1.1rem; opacity: 0.9;">≈ {predicted_time/60:.1f} hours</div>
                            
                            <div class="time-breakdown">
                                <div class="time-component">
                                    <div class="time-component-value">🍳 {prep_time:.0f}</div>
                                    <div class="time-component-label">Cooking Time</div>
                                </div>
                                <div class="time-component">
                                    <div style="font-size: 2rem;">+</div>
                                </div>
                                <div class="time-component">
                                    <div class="time-component-value">🚗 {estimated_delivery:.0f}</div>
                                    <div class="time-component-label">Delivery Time</div>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Distance info
                    if "calculated_distance_km" in result:
                        distance = result['calculated_distance_km']
                        avg_speed = (distance / estimated_delivery) * 60 if estimated_delivery > 0 else 0
                        
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-value">📏 {distance:.2f}</div>
                                    <div class="metric-label">Distance (km)</div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col_m2:
                            st.markdown(f"""
                                <div class="metric-card">
                                    <div class="metric-value">⚡ {avg_speed:.1f}</div>
                                    <div class="metric-label">Avg Speed (km/h)</div>
                                </div>
                            """, unsafe_allow_html=True)
                    
                    # Detailed Breakdown
                    st.subheader("📊 Detailed Analysis")
                    st.markdown(f"""
                        <div class="info-card">
                            <strong>🍔 Order Context</strong><br>
                            <span class="feature-badge">{order_type}</span>
                            <span class="feature-badge">{vehicle_type}</span>
                            <span class="feature-badge">{city_type}</span>
                            {"<span class='feature-badge'>🎉 Festival</span>" if festival == "Yes" else ""}
                            <br><br>
                            <strong>🌦️ Conditions</strong><br>
                            <span class="feature-badge">Weather: {weather}</span>
                            <span class="feature-badge">Traffic: {traffic}</span>
                            {"<span class='feature-badge'>🚦 Rush Hour</span>" if is_rush_hour_int else ""}
                            {"<span class='feature-badge'>🎉 Weekend</span>" if is_weekend_int else ""}
                            <br><br>
                            <strong>👤 Delivery Partner</strong><br>
                            Age: {delivery_age} | Rating: {delivery_rating} ⭐ | Condition: {vehicle_condition}/3
                            {"<br><br><strong>📦 Multiple Deliveries:</strong> " + str(multiple_deliveries) if multiple_deliveries > 0 else ""}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Success message with context
                    if predicted_time < 20:
                        st.balloons()
                        st.markdown("""
                            <div class="success-box">
                                ⚡ <strong>Super Fast Delivery!</strong><br>
                                Your order will arrive very quickly.
                            </div>
                        """, unsafe_allow_html=True)
                    elif predicted_time < 35:
                        st.markdown("""
                            <div class="success-box">
                                ✅ <strong>Good Delivery Time!</strong><br>
                                Standard delivery window.
                            </div>
                        """, unsafe_allow_html=True)
                    elif predicted_time < 50:
                        st.markdown("""
                            <div class="warning-box">
                                ⏰ <strong>Moderate Wait Time</strong><br>
                                Slightly longer than average due to current conditions.
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                            <div class="warning-box">
                                ⏰ <strong>Extended Wait Time</strong><br>
                                High traffic or long distance may cause delays.
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # ETA time
                    estimated_arrival = datetime.combine(order_date, order_time)
                    from datetime import timedelta
                    estimated_arrival += timedelta(minutes=predicted_time)
                    st.info(f"🕐 **Estimated Arrival:** {estimated_arrival.strftime('%I:%M %p')}")
                
                else:
                    st.error(f"❌ Prediction failed: {response.json().get('detail', 'Unknown error')}")
            
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Make sure FastAPI is running!")
                st.code(f"uvicorn main:app --reload", language="bash")
            
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. API might be slow or down.")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.code(str(e))
    
    st.divider()
    
    # API Status Check
    st.subheader("🔍 System Status")
    if st.button("Check API Health", use_container_width=True):
        try:
            health = requests.get(f"{api_base_url}/", timeout=5)
            if health.status_code == 200:
                data = health.json()
                st.success("✅ API is running!")
                st.json(data)
            else:
                st.error("❌ API returned error")
        except:
            st.error("❌ Cannot reach API")
            st.info("Make sure FastAPI server is running on the configured URL")

# Footer
st.divider()
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h4>🧠 Model Features</h4>
            <p style="font-size: 0.9rem; color: #666;">
            • Distance calculation<br>
            • Rush hour detection<br>
            • Weather impact<br>
            • Traffic analysis
            </p>
        </div>
    """, unsafe_allow_html=True)

with col_f2:
    st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h4>📊 Accuracy</h4>
            <p style="font-size: 0.9rem; color: #666;">
            • XGBoost ML Model<br>
            • ~5-8 min MAE<br>
            • 75-85% R² Score<br>
            • Outlier filtered
            </p>
        </div>
    """, unsafe_allow_html=True)

with col_f3:
    st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h4>⚡ Performance</h4>
            <p style="font-size: 0.9rem; color: #666;">
            • Real-time predictions<br>
            • Sub-second response<br>
            • Scalable API<br>
            • Production ready
            </p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem; margin-top: 1rem; border-top: 2px solid #eee;">
        <p>🤖 Powered by XGBoost & Machine Learning | 🚀 Built with FastAPI & Streamlit</p>
        <p style="font-size: 0.9rem;">Made with ❤️ for accurate delivery time predictions</p>
    </div>
""", unsafe_allow_html=True)