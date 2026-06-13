import os
import boto3
import json
import time  #  Added for pausing execution

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv
from botocore.exceptions import ClientError  #  Added to catch specific AWS errors

# 1. Load AWS Credentials
load_dotenv()
# Provide a fallback string or an empty string to prevent crashes
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# AWS looks for AWS_DEFAULT_REGION
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")

# Initialize Bedrock Client targeting us-east-1
bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")

class BedrockTitanEmbeddings(Embeddings):
    """Resilient custom wrapper that handles AWS Bedrock throttling automatically."""
    def embed_documents(self, texts):
        embeddings = []
        for i, text in enumerate(texts):
            safe_text = text.replace('"', '\\"').replace('\n', ' ')
            body = json.dumps({"inputText": safe_text})
            
            # --- EXPONENTIAL BACKOFF MECHANISM ---
            retries = 0
            max_retries = 5
            delay = 2  # Start with a 2-second pause if throttled
            
            while retries < max_retries:
                try:
                    response = bedrock_runtime.invoke_model(
                        modelId="amazon.titan-embed-text-v1",
                        contentType="application/json",
                        accept="application/json",
                        body=body
                    )
                    response_body = json.loads(response['body'].read().decode('utf-8'))
                    embeddings.append(response_body['embedding'])
                    
                    # Add a gentle pacing delay between successful calls to stay safe under sandbox limits
                    time.sleep(1.5)
                    break  # Success! Break out of the retry loop for this chunk
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == 'ThrottlingException':
                        print(f" [THROTTLED] AWS rate limit hit on chunk {i+1}/{len(texts)}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2  # Exponentially double the wait time (2s -> 4s -> 8s...)
                        retries += 1
                    else:
                        raise e  # If it's a different error (like access denied), fail immediately
            else:
                raise Exception(f" Max retries exceeded. Failed to embed chunk due to strict AWS throttling.")
                
        return embeddings

    def embed_query(self, text):
        return self.embed_documents([text])[0]

print(" Reading private corporate documents...")
with open("knowledge/company_policy.txt", "r") as f:
    raw_document = f.read()

print(" Splitting document into optimized text chunks...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
chunks = text_splitter.split_text(raw_document)

print(f" Sending {len(chunks)} text chunks to Amazon Bedrock...")
embeddings_engine = BedrockTitanEmbeddings()

# Build and compile our vector directory
vector_store = FAISS.from_texts(chunks, embeddings_engine)

print(" Saving Vector Database Index locally as 'faiss_index'...")
vector_store.save_local("faiss_index")

print(" Ingestion Pipeline Complete! Your documentation is now fully vectorized.")