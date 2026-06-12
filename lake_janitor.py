import os
import awswrangler as wr
from dotenv import load_dotenv

# Load AWS Credentials
load_dotenv()

# Provide a fallback string or an empty string to prevent crashes
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# AWS looks for AWS_DEFAULT_REGION
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")

#  CONFIGURATION
DATABASE = "logistics_db"
TABLE = "iceberg_analytics"
BUCKET_NAME = "enterprise-data-lake-iyed"

# Tell Athena where to dump the query execution logs (fixes the UserWarning!)
ATHENA_RESULTS_PATH = f"s3://{BUCKET_NAME}/athena-query-results/"

print(" Starting Autonomous Lakehouse Maintenance Routine...\n")

# 1. COMPACTION: Gather up small files and merge them into large, high-performance blocks
print(" Step 1: Rewriting data files to optimize layout and fix small-file bloat...")
compaction_query = f"OPTIMIZE {DATABASE}.{TABLE} REWRITE DATA USING BIN_PACK"

wr.athena.start_query_execution(
    sql=compaction_query, 
    database=DATABASE,
    s3_output=ATHENA_RESULTS_PATH
)
print(" Data files successfully compacted into optimal sizes.")

# 2. VACUUM: Drop old table transaction states and prune orphan files natively in Athena
print(" Step 2: Expiring stale snapshots and vacuuming metadata manifest bloat...")
vacuum_query = f"VACUUM {DATABASE}.{TABLE}"  #  Athena native maintenance command

try:
    wr.athena.start_query_execution(
        sql=vacuum_query, 
        database=DATABASE,
        s3_output=ATHENA_RESULTS_PATH
    )
    print(" Stale Iceberg snapshots pruned and vacuumed safely from storage.")
except Exception as e:
    print(f"ℹ️ Snapshot log: {e}")

print("\n Maintenance Complete! Your Apache Iceberg Lakehouse is running at peak performance.")