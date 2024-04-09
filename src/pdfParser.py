import os
from dotenv import load_dotenv
from llama_parse import LlamaParse

load_dotenv()

def parsePDF(file_name):
    parser = LlamaParse(
        api_key=os.getenv("LLAMA_CLOUD_API_KEY"), 
        result_type="markdown" 
    )

    documents = parser.load_data(f"/Users/ejiang/Desktop/Evan Spring 2024/sandbox-projects/uploadedFiles/{file_name}")

    with open(f"{file_name}.md", "w") as f: 
        f.write(str(documents[0].text))