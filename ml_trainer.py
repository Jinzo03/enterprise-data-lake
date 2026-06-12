import os
import pickle
import awswrangler as wr
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from dotenv import load_dotenv

# 1. Load AWS Credentials
load_dotenv()
# Provide a fallback string or an empty string to prevent crashes
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# AWS looks for AWS_DEFAULT_REGION
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")

print(" Fetching historical Lakehouse records for training...")
df = wr.athena.read_sql_query(
    sql="SELECT temperature_celsius, container_weight_kg, status FROM logistics_db.iceberg_analytics",
    database="logistics_db",
    ctas_approach=False
)

if len(df) < 5:
    print(" Not enough data to train yet! Run your stream producer for a bit longer first.")
    exit()

print(f" Training Machine Learning Model over {len(df)} production records...")

# Convert target status into a binary category: 1 if DELAYED, 0 otherwise
df['is_delayed'] = (df['status'] == 'DELAYED').astype(int)

# Feature selection
X = df[['temperature_celsius', 'container_weight_kg']]
y = df['is_delayed']

# Train a Random Forest Classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# Save the trained model to disk
with open("delay_predictor.pkl", "wb") as f:
    pickle.dump(model, f)

print(" ML Training Complete! Model file saved as 'delay_predictor.pkl'")