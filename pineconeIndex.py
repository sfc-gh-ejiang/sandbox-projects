import os
from dotenv import load_dotenv
import pinecone
import time
from tqdm.auto import tqdm

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
MODEL = os.getenv("MODEL")

def initialize_pinecone(index_name):
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    spec = pinecone.ServerlessSpec(cloud="gcp-starter", region="us-central-1")

    # If there's no index initialized already
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            index_name,
            dimension=1536, # default for text-embedding-3-small
            metric='cosine',
            spec=spec
        )
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)

    index = pc.Index(index_name)
    return index

def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.readlines()

def create_and_upsert_embeddings(client, index, text_md, code_md, batch_size=32):
    count = 0
    text_lines = read_markdown_file(text_md)
    code_lines = read_markdown_file(code_md)
    lines = text_lines + code_lines

    for i in tqdm(range(0, len(lines), batch_size)):
        i_end = min(i + batch_size, len(lines))
        lines_batch = lines[i: i_end]
        ids_batch = [f"{count}_{n}" for n in range(i, i_end)]

        res = client.embeddings.create(input=lines_batch, model=MODEL)
        embeds = [record['embedding'] for record in res['data']]

        meta = [{'text': line, 'type': 'text' if i < len(text_lines) else 'code'} for line in lines_batch]
        to_upsert = zip(ids_batch, embeds, meta)
        index.upsert(vectors=list(to_upsert))

        count += len(lines_batch)