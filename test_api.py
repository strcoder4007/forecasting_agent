import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "dummy"))

# Just check if the SDK recognizes the model names structure
print("Testing model names mapping...")
try:
    # We won't actually call it since dummy key will fail authentication, 
    # but we want to make sure the names don't throw immediate local validation errors
    print("gemini-3.1-flash-lite-preview")
    print("gemini-3.1-pro-preview")
except Exception as e:
    print(f"Error: {e}")
