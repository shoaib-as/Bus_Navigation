from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor
import joblib
from .build_dataset import build_training_dataset

def train_model():
    df = build_training_dataset()
    if df.empty:
        print("⚠️ No training data available.")
        return

    X = df.drop(columns=["eta_minutes"])
    y = df["eta_minutes"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Mean Absolute Error: {mae:.2f} minutes")

    # Save model
    joblib.dump(model, "ml_model/bus_eta_model.pkl")
    print("✅ Model trained and saved.")
