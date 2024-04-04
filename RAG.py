import os
from dotenv import load_dotenv
from pineconeIndex import initialize_pinecone

load_dotenv()
MODEL = os.getenv("MODEL")
INDEX_NAME = os.getenv("INDEX_NAME")

def generate_response(client, query):
    index = initialize_pinecone(INDEX_NAME)

    # Query and response logic
    xq = client.embeddings.create(input=query, model=MODEL).data[0].embedding
    res = index.query(vector=[xq], top_k=5, include_metadata=True)
    
    # Generate response using OpenAI
    context_documents = "\n".join([f"Document {i+1}: {match['metadata']['text']}" for i, match in enumerate(res['matches'])])
    system_prompt = "You are an assistant that provides detailed technical help in code based on provided documents. Use the information from the documents to answer the user's question. Please include an example with code."
    user_question = f"{query}\n\n{context_documents}"

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ],
    )

    return completion.choices[0].message.content