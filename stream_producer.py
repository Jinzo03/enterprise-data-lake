import os
import time
import random
import uuid
from datetime import datetime
import awswrangler as wr
from dotenv import load_dotenv

# 1. Load AWS Credentials
load_dotenv()
# Provide a fallback string or an empty string to prevent crashes
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# AWS looks for AWS_DEFAULT_REGION
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")

def generate_log_event():
    """Generates a mock shipping container telemetry event."""
    routes = ["NY-LON", "TOK-SF", "PAR-BER", "SHG-LA"]
    status_options = ["IN_TRANSIT", "CUSTOMS_HOLD", "DELIVERED", "DELAYED"]
    
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "route": random.choice(routes),
        "status": random.choice(status_options),
        "temperature_celsius": round(random.uniform(-5.0, 15.0), 2),
        "container_weight_kg": random.randint(1000, 5000)
    }

print("Starting Cost-Free Real-Time Python Streaming Engine...")
print("Streaming records directly to Apache Iceberg via Athena micro-batches.")
print("Press Ctrl+C to stop.\n")

BATCH_SIZE = 5  # Collect 5 records before pushing to the cloud
memory_batch = []

try:
    while True:
        # 1. Generate live event and save to memory
        event = generate_log_event()
        memory_batch.append(event)
        print(f" Generated Event [{event['event_id'][:8]}] - Route: {event['route']}")
        
        # 2. Once we hit our batch size, stream them to Iceberg!
        if len(memory_batch) >= BATCH_SIZE:
            print("\n Batch full! Streaming micro-batch to Apache Iceberg...")
            
            # Construct a multi-row SQL INSERT statement
            values_list = []
            for e in memory_batch:
                values_list.append(
                    f"('{e['event_id']}', '{e['timestamp']}', '{e['status']}', "
                    f"{e['temperature_celsius']}, {e['container_weight_kg']}, '{e['route']}')"
                )
            
            sql_query = f"""
                INSERT INTO logistics_db.iceberg_analytics 
                (event_id, timestamp, status, temperature_celsius, container_weight_kg, route)
                VALUES {', '.join(values_list)}
            """
            
            # Execute the query directly on Athena
            wr.athena.start_query_execution(
                sql=sql_query,
                database="logistics_db"
            )
            
            print(" Micro-batch safely written to Iceberg Lakehouse storage!\n")
            memory_batch = [] # Clear memory for next batch
            
        time.sleep(1.5) # Wait between simulations

except KeyboardInterrupt:
    print("\n Streaming stopped by user.")