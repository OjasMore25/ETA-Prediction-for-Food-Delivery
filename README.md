# ETA Predictor 🚖⏱️

## 📌 Project Overview
This project aims to build a **machine learning-based ETA (Estimated Time of Arrival) predictor**.  
The task is framed as a **regression problem**, where the model learns from trip/ride data and predicts the expected journey time.  

---

## ⚙️ Workflow
### 1. Data Preprocessing
- **Data Cleaning**
  - Removed duplicates and missing values.
  - Dropped irrelevant columns that don’t affect ETA prediction.
- **Feature Engineering**
  - Encoded categorical variables using Label Encoding / One-Hot Encoding.
  - Normalized/standardized numerical features for better model convergence.
  - Extracted temporal features (hour of day, weekday, etc.) to capture time-based patterns.
- **Train-Test Split**
  - Dataset split into **train (80%)** and **test (20%)** sets.

---

### 2. Algorithms Implemented
The following machine learning models were trained and compared:

1. **Linear Regression**
   - Used as a baseline model.
   - Provides quick interpretability but struggles with non-linear patterns.

2. **Random Forest Regressor**
   - Ensemble of decision trees.
   - Improved accuracy and robustness compared to a single tree.

3. **XGBoost Regressor**
   - Gradient boosting framework with strong performance on tabular data.
   - Handles bias-variance trade-off efficiently.

4. **LightGBM Regressor**
   - Gradient boosting optimized for speed and efficiency.
   - Works well with large-scale data and categorical variables.

5. **CatBoost Regressor**
   - Boosting algorithm designed to handle categorical data automatically.
   - Reduces need for extensive preprocessing.

---

### 3. Model Evaluation
Metrics used to evaluate models:
- **Mean Absolute Error (MAE):** Average magnitude of prediction errors.  
- **Root Mean Squared Error (RMSE):** Penalizes larger errors more heavily.  
- **R² Score:** Measures variance explained by the model.  

#### 📊 Results (Test Set)
| Model              | R² Score | MAE    | RMSE   |
|--------------------|----------|--------|--------|
| Linear Regression  | **0.8324** | **6.0162** | **9.1602** |
| Random Forest      | 0.7945   | 6.9079 | 10.1435 |
| XGBoost            | 0.8176   | 6.2862 | 9.5559 |
| LightGBM           | 0.8101   | 6.6081 | 9.7523 |
| CatBoost           | 0.8140   | 6.4852 | 9.6501 |

---

### 4. Insights
- **Linear Regression surprisingly gave the best R², MAE, and RMSE**, showing strong baseline performance.  
- **Random Forest** underperformed slightly compared to boosting methods, likely due to less tuning.  
- **XGBoost, LightGBM, and CatBoost** were close contenders, with XGBoost achieving the best balance among ensemble methods.  
- Overall, **Linear Regression outperformed tree-based methods** on this dataset, which suggests:
  - The dataset may have strong linear relationships.
  - Feature engineering already captured much of the variance.  

---

## 🔮 Future Improvements
To further enhance the ETA predictor:

### Feature Engineering
- Incorporate **geospatial features** (distance, routes, traffic density).  
- Add **external data sources**: real-time traffic, weather, holiday info.  

### Model Improvements
- Perform **hyperparameter tuning** (GridSearchCV, RandomizedSearch, Bayesian Optimization).  
- Explore **deep learning models**:
  - LSTMs/Transformers for sequential time-series data.
  - Graph Neural Networks for road networks.  

### Deployment
- Package into a **REST API** for real-time ETA prediction.  
- Deploy on **cloud platforms (AWS/GCP/Azure)** with autoscaling.  

### Monitoring & Maintenance
- Track **model drift** and retrain with fresh data.  
- Build a **dashboard** for monitoring ETA prediction accuracy.  

---

## ✅ Conclusion
- Multiple regression algorithms were implemented and compared for ETA prediction.  
- **Linear Regression surprisingly outperformed ensemble models** on this dataset.  
- With additional contextual features (traffic, weather, geospatial data), tree-based ensembles and deep learning models are expected to perform better in real-world conditions.  

---

## Dataset used
-Kaggle's Food_Delivery_Times.csv
