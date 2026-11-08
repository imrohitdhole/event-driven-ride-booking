import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Resolve paths relative to this file so the script works from any directory
HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(HERE, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "fare_predictor.pkl")  # loaded by fare_api.py

# Load dataset
df = pd.read_csv(os.path.join(HERE, "uber.csv"))

# Drop nulls and filter outliers
df = df.dropna()
df = df[(df['fare_amount'] > 0) & (df['fare_amount'] < 100)]

# Feature engineering: calculate distance
def haversine(lat1, lon1, lat2, lon2):
    import numpy as np
    R = 6371  # km
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

# Distance in miles, matching the distanceInMiles value the backend sends to /predict
KM_TO_MILES = 0.621371
df['distance'] = haversine(df['pickup_latitude'], df['pickup_longitude'],
                           df['dropoff_latitude'], df['dropoff_longitude']) * KM_TO_MILES

# Extract hour from datetime
df['pickup_datetime'] = pd.to_datetime(df['pickup_datetime'])
df['hour'] = df['pickup_datetime'].dt.hour

# Prepare input/output
X = df[['distance', 'passenger_count', 'hour']]
y = df['fare_amount']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Model pipeline
model = Pipeline([
    ('scaler', StandardScaler()),
    ('regressor', RandomForestRegressor(n_estimators=100))
])

model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
import numpy as np
print("✅ RMSE:", np.sqrt(mean_squared_error(y_test, preds)))

# Save model
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(model, MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
