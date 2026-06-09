import os
import pandas as pd
import matplotlib.pyplot as plt
import awswrangler as wr
from dotenv import load_dotenv

# 1. Load AWS Credentials from your existing .env file
load_dotenv()

# Provide a fallback string or an empty string to prevent crashes
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# AWS looks for AWS_DEFAULT_REGION
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")

print("🔄 Querying live Data Lake via Amazon Athena...")

# 2. Run the SQL Query directly from Python
query = """
    SELECT route, status, temperature_celsius, timestamp 
    FROM raw_logs
"""

# AWS Wrangler handles the Athena polling and S3 downloads automatically!
df = wr.athena.read_sql_query(
    sql=query,
    database="logistics_db",
    ctas_approach=False
)

print(f" Successfully downloaded {len(df)} live logistics records!\n")
print(df.head()) # Print the first 5 rows to the console

# 3. Create a Visualization Dashboard
print("\n Generating dashboard...")

# Set up a figure with 2 subplots (side-by-side)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Global Logistics Live Data Lake Dashboard', fontsize=16)

# Chart 1: Shipment Status Counts
status_counts = df['status'].value_counts()
status_counts.plot(kind='bar', ax=ax1, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
ax1.set_title('Current Shipment Statuses')
ax1.set_ylabel('Number of Containers')
ax1.tick_params(axis='x', rotation=45)

# Chart 2: Average Temperature by Route
avg_temp = df.groupby('route')['temperature_celsius'].mean()
avg_temp.plot(kind='bar', ax=ax2, color='#9467bd')
ax2.set_title('Average Container Temperature by Route')
ax2.set_ylabel('Temperature (°C)')
ax2.tick_params(axis='x', rotation=45)

# Adjust layout and display the charts!
plt.tight_layout()
plt.show()