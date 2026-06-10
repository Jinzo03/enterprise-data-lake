import os
import awswrangler as wr
from dotenv import load_dotenv

# 1. Load AWS Credentials
load_dotenv()
# Provide a fallback string or an empty string to prevent crashes
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# AWS looks for AWS_DEFAULT_REGION
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")
#  CONFIGURATION - Update with your bucket name!
BUCKET_NAME = "enterprise-data-lake-iyed"

print(" Extracting raw JSON logs from S3...")
raw_query = "SELECT * FROM logistics_db.raw_logs"

# Read all current raw logs into a dataframe
df = wr.athena.read_sql_query(
    sql=raw_query,
    database="logistics_db",
    ctas_approach=False
)

print(f"🔄 Transforming {len(df)} rows into optimized Columnar Parquet format...")

# 2. Write the data back to S3 as an optimized Parquet dataset
# AWS Wrangler handles the binary compilation and cataloging automatically!
wr.s3.to_parquet(
    df=df,
    path=f"s3://{BUCKET_NAME}/analytics/",
    dataset=True,
    database="logistics_db",
    table="optimized_analytics",
    mode="overwrite"
)

print("ETL Job Complete! New table 'optimized_analytics' registered in Glue Data Catalog.")