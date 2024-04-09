import os
from dotenv import load_dotenv
import pinecone
import time
from tqdm.auto import tqdm

load_dotenv()

def initialize_pinecone(index_name):
    pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
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

def create_and_upsert_embeddings(iteration_id, client, index, markdown, batch_size=32):
    count = 0
    lines = read_markdown_file(markdown) 

    for i in tqdm(range(0, len(lines), batch_size)):
        i_end = min(i + batch_size, len(lines))
        lines_batch = lines[i: i_end]
        ids_batch = [f"{iteration_id}_{count}_{n}" for n in range(i, i_end)]

        res = client.embeddings.create(input=lines_batch, model=os.getenv("MODEL"))
        embeds = [record.embedding for record in res.data]
        meta = [{'text': line, 'type': 'text'} for line in lines_batch]

        to_upsert = list(zip(ids_batch, embeds, meta))

        print("LENGTH: ", len(to_upsert))

        index.upsert(vectors=to_upsert)

        print("SUCCESS")

        count += len(lines_batch)