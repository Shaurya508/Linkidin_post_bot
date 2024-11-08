from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json

GOOGLE_API_KEY = "AIzaSyD04HAUVodSnvfXlWmxEvBsXpJzZ_7IKnM"

print("Before defining the function")

def create_faiss_db(chunks, db_name):
    
    # Ensure the GOOGLE_API_KEY is set
    google_api_key = GOOGLE_API_KEY
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    chunks_1 = [
    {
        "content": item["content"].lower(),
        "metadata": item["metadata"]
    }
    for item in chunks        
    ]
    
    # Initialize the embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key = google_api_key)
    
    # Prepare the texts and metadatas
    texts = [chunk['content'] for chunk in chunks_1]
    metadatas = [chunk['metadata'] for chunk in chunks_1]
    
    # Create the FAISS index
    vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    
    # Save the index locally
    vector_store.save_local(db_name)
    
    print(f"FAISS database created and saved as '{db_name}'")
    return vector_store

print("After defining the function")



with open('all_chunks.json', 'r') as file:
    all_chunks_linkedin = json.load(file)

with open('all_chunks_stack_exchange.json', 'r') as file:
    all_chunks_stack_exchange = json.load(file)

with open('stat_chunk_v1_2.json', 'r') as file:
    all_chunks_wiki = json.load(file)

chunks1 = all_chunks_linkedin + all_chunks_stack_exchange

chunks2 = all_chunks_wiki


print("Loaded all the chunks, now moving on to executing function to create the two vector DBs")

#create_faiss_db(chunks1, db_name="Link_Stack_DB")

print("DB made for LinkedIn and Stack Exchange content")

create_faiss_db(chunks2, db_name="Wiki_DB-gemini-trial_v1")

print("DB made for Wiki content")
print("=============================== DONE ===============================")