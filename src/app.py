import streamlit as st
import os
from dotenv import load_dotenv
from pineconeIndex import initialize_pinecone, create_and_upsert_embeddings
from openai import AzureOpenAI
from pathlib import Path
from pdfParser import parsePDF
import time

load_dotenv()

index = initialize_pinecone(os.getenv("INDEX_NAME"))

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OAI_API_KEY"),
    api_version="2023-09-01-preview"
)

if 'files_uploaded' not in st.session_state:
    st.session_state['files_uploaded'] = False

def stream_data(response):
    for word in response.split(" "):
        yield word + " "
        time.sleep(0.02)

st.title('Enterprise RAG (Demo)')

files = st.file_uploader(label = " ", type=["pdf"], accept_multiple_files=True)

if files and not st.session_state['files_uploaded']: 
    st.session_state['files_uploaded'] = False
    iteration_id = 0
    for file in files:
        save_folder = '/Users/ejiang/Desktop/Evan Spring 2024/sandbox-projects/uploadedFiles'
        save_path = Path(save_folder, file.name)
        with open(save_path, mode='wb') as w:
            w.write(file.getvalue())

        if save_path.exists():
            st.success(f'File {file.name} is successfully saved!')

        parsePDF(file.name)
        markdown_file = f"{file.name}.md"
        create_and_upsert_embeddings(iteration_id, client, index, markdown_file)
        iteration_id += 1

    st.session_state['files_uploaded'] = True

system_prompt = '''
    You are an assistant that provides detailed technical help based on the provided documents. 
    Use the information from the documents to answer the user's question. Please be very concise, keeping the 
    response as short and clear as possible. Use the documents for context, and only use the documents if they help answer the question.
'''

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything."):
    # Query and response logic
    xq = client.embeddings.create(input=prompt, model=os.getenv("MODEL")).data[0].embedding
    top_five_matches = index.query(vector=[xq], top_k=5, include_metadata=True)
    relevant_matches = []

    print(top_five_matches)

    for match in top_five_matches['matches']:
        if match['score'] >= 0.75:
            relevant_matches.append(match)
        else:
            break

    res = {'matches' : relevant_matches}

    print("RES: ", res)
    
    # Generate response using OpenAI
    context_documents = "\n".join([f"Document {i+1}: {match['metadata']['text']}" for i, match in enumerate(res['matches'])])
    user_prompt = f"{prompt}\n\n{context_documents}"

    print("USER PROMPT: ", user_prompt)

    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="SnowQA",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
        ).choices[0].message.content
        st.write_stream(stream_data(response))

    st.session_state.messages[-1]["content"] = prompt

    print("RESPONSE: ", response)

    st.session_state.messages.append({"role": "assistant", "content": response})

    for m in st.session_state.messages:
        print({"role": m["role"], "content": m["content"]})