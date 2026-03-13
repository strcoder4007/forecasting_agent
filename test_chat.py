import sys
from backend.chat_service import ChatService
from backend.data_loader import DataLoader

cs = ChatService(DataLoader())
# Set dummy API key to see if it makes the right call structure 
try:
    print(cs.chat("Run a new forecast", None))
except Exception as e:
    print(f"Error: {e}")
