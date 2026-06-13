import os
import boto3
import json
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv

# Load AWS Credentials
load_dotenv()
# Provide a fallback string or an empty string to prevent crashes
os.environ["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID", "")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# AWS looks for AWS_DEFAULT_REGION
os.environ["AWS_DEFAULT_REGION"] = os.environ.get("AWS_REGION", "eu-north-1")

#  FIX: Explicitly target us-east-1 for cross-region inference
bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name="us-east-1")

class BedrockTitanEmbeddings(Embeddings):
    """Embeddings utility for matching real-time queries against our indexed database."""
    def embed_documents(self, texts):
        embeddings = []
        for text in texts:
            body = json.dumps({"inputText": text.replace('"', '\\"').replace('\n', ' ')})
            response = bedrock_runtime.invoke_model(
                modelId="amazon.titan-embed-text-v1", contentType="application/json", accept="application/json", body=body
            )
            embeddings.append(json.loads(response['body'].read().decode('utf-8'))['embedding'])
        return embeddings
    def embed_query(self, text):
        return self.embed_documents([text])[0]

print(" Loading local Serverless Vector Database index...")
embeddings_engine = BedrockTitanEmbeddings()
vector_store = FAISS.load_local("faiss_index", embeddings_engine, allow_dangerous_deserialization=True)

# Define your user prompt here!
user_query = "What is the secret server room door passcode?"

print(f" Searching database for facts related to: '{user_query}'...")
relevant_docs = vector_store.similarity_search(user_query, k=1)
context_text = relevant_docs[0].page_content
print(f" Found relevant documentation fact:\n   ➡️ \"{context_text}\"\n")

# Wrap context inside an strict engineering prompt
prompt = f"""
You are a secure corporate assistant. Use ONLY the following context to answer the question. 
If the answer is not in the context, say "I do not know".

Context:
{context_text}

Question: {user_query}
Answer:"""

print(" Invoking Amazon Bedrock Text Generation Model...")
response = bedrock_runtime.invoke_model(
    modelId="amazon.titan-text-express-v1",
    contentType="application/json",
    accept="application/json",
    body=json.dumps({
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 150,
            "temperature": 0.0, # 0.0 ensures highly accurate, deterministic outputs without creativity
            "topP": 0.9
        }
    })
)

result = json.loads(response['body'].read().decode('utf-8'))
output_text = result['results'][0]['outputText']

print("\n --- AI RESPONSE --- ")
print(output_text.strip())
print("─────────────────────────")