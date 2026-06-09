import os
import boto3
import json
import time
import random
from datetime import datetime
import uuid
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Quick sanity check to make sure the environment variables loaded
if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, BUCKET_NAME]):
    raise ValueError("Missing environment variables! Please check your .env file.")

# Initialize the S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def generate_log_event():
    """Creates a fake JSON log for a logistics network."""
    event_id = str(uuid.uuid4())
    routes = ["NY-LON", "TOK-SF", "PAR-BER", "SHG-LA"]
    status_options = ["IN_TRANSIT", "CUSTOMS_HOLD", "DELIVERED", "DELAYED"]

    log_data = {
        "event_id": event_id,
        "timestamp": datetime.utcnow().isoformat(),
        "route": random.choice(routes),
        "status": random.choice(status_options),
        "temperature_celsius": round(random.uniform(-5.0, 15.0), 2),
        "container_weight_kg": random.randint(1000, 5000)
    }
    return log_data

print(f"Starting Secure Data Ingestion Pipeline to S3 Bucket: {BUCKET_NAME}...")

# Generate and upload 5 files to test the pipeline
for i in range(1, 6):
    event = generate_log_event()
    json_data = json.dumps(event)

    file_name = f"raw-logs/log_{int(time.time() * 1000)}_{event['event_id'][:8]}.json"

print(f"Uploading file {file_name} to S3...") 
s3_client.put_object(
    Bucket=BUCKET_NAME,
    Key=file_name,
    Body=json_data,
    ContentType='application/json',
) 

time.sleep(2)  # Sleep to ensure unique timestamps for file names

print(" Pipeline run complete! 5 records securely ingested into S3.")