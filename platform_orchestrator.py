import os
import time
import random
import uuid
import pickle
from datetime import datetime
import awswrangler as wr
from dotenv import load_dotenv

# Load Environment
load_dotenv()
# Provide a fallback string or an empty string to prevent crashes
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# AWS looks for AWS_DEFAULT_REGION
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")

# Load our pre-trained ML Model
with open("delay_predictor.pkl", "rb") as f:
    ml_model = pickle.load(f)

def run_data_quality_checks(event):
    """PILLAR 1: Data Quality Bouncer Layer."""
    # Rule A: Temperature sensor malfunction check
    if event['temperature_celsius'] > 60.0 or event['temperature_celsius'] < -60.0:
        return False, "CRITICAL_ANOMALY: Temperature out of physical sensor boundaries."
    # Rule B: Missing identification metrics
    if not event['event_id']:
        return False, "MALFORMED_DATA: Missing unique event identifier."
    return True, "PASSED"

def generate_telemetry_event():
    """Simulates real-time telemetry extraction."""
    routes = ["NY-LON", "TOK-SF", "PAR-BER", "SHG-LA"]
    status_options = ["IN_TRANSIT", "CUSTOMS_HOLD", "DELIVERED", "DELAYED"]
    
    # Intentionally inject bad data 15% of the time to test our Quality Bouncer!
    is_corrupt = random.random() < 0.15
    temp = random.uniform(100.0, 150.0) if is_corrupt else random.uniform(-5.0, 15.0)

    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "route": random.choice(routes),
        "status": random.choice(status_options),
        "temperature_celsius": round(temp, 2),
        "container_weight_kg": random.randint(1000, 5000)
    }

print(" Enterprise Data Platform Orchestrator Activated...\n")

try:
    while True:
        print("--- New Pipeline Execution Cycle Triggered ---")
        
        # Step 1: Ingestion / Extraction
        raw_event = generate_telemetry_event()
        print(f"[STAGE 1: INGEST] Captured tracking packet for Route: {raw_event['route']}")
        
        # Step 2: Orchestrated Data Quality Validation
        is_valid, validation_msg = run_data_quality_checks(raw_event)
        if not is_valid:
            print(f" [STAGE 2: QUALITY CRASH] {validation_msg}")
            
            raw_event['quarantine_reason'] = validation_msg
            raw_event['quarantine_timestamp'] = datetime.utcnow().isoformat()
            
            quarantine_path = f"s3://enterprise-data-lake-iyed/quarantine/{raw_event['event_id']}.json"
            
            import pandas as pd
            bad_df = pd.DataFrame([raw_event])
            wr.s3.to_json(df=bad_df, path=quarantine_path)
            
            print(f" [OBSERVABILITY] Corrupt payload isolated at: {quarantine_path}\n")
            time.sleep(2)
            continue

        # Step 3: Predictive ML Inference Integration
        features = [[raw_event['temperature_celsius'], raw_event['container_weight_kg']]]
        # Calculate the live probability that this exact package will become delayed
        delay_probability = ml_model.predict_proba(features)[0][1]
        
        # Enrich the original payload with the ML score on the fly!
        raw_event['predicted_delay_risk'] = round(float(delay_probability * 100), 2)
        print(f" [STAGE 3: ML ENRICHMENT] Model appends Delay Risk Score: {raw_event['predicted_delay_risk']}%")

        # Step 4: Loading into Transactional Lakehouse Storage
        sql_query = f"""
            INSERT INTO logistics_db.iceberg_analytics 
            (event_id, timestamp, status, temperature_celsius, container_weight_kg, route)
            VALUES ('{raw_event['event_id']}', '{raw_event['timestamp']}', '{raw_event['status']}', 
                    {raw_event['temperature_celsius']}, {raw_event['container_weight_kg']}, '{raw_event['route']}')
        """
        wr.athena.start_query_execution(sql=sql_query, database="logistics_db")
        print(" [STAGE 4: LAKEHOUSE LOAD] Safely committed record to Apache Iceberg via Athena.\n")
        
        time.sleep(3)

except KeyboardInterrupt:
    print("\n Orchestration engine spun down safely.")