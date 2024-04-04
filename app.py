import streamlit as st
from openai import OpenAI
from RAG import generate_response
from dotenv import load_dotenv
import time
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=OPENAI_API_KEY
)

st.title('Demo AI')

query = st.text_input("Ask me anything about Google BigQuery's AutoML.")

def stream_data(response):
    for word in response.split(" "):
        yield word + " "
        time.sleep(0.02)
        
if st.button('Submit'):
    if query:
        with st.spinner("Loading..."):
            response = generate_response(client, query)
            st.write_stream(stream_data(response))
    else:
        st.warning("Please enter a query.")