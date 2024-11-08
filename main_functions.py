from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
import os
# from PyPDF2 import PdfReader #used it before now using tesseract
import requests
from bs4 import BeautifulSoup
# from dotenv import load_dotenv
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
import pandas as pd
from langchain.retrievers.multi_query import MultiQueryRetriever
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import ConversationalRetrievalChain
# from langchain.chains import ConversationChain
from pdf2image import convert_from_path
# from PIL import Image
import streamlit as st
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import re
import json

GOOGLE_API_KEY = "AIzaSyC2sy1EuJs3OeM8yQXDrhf7xHuNd1_5L-Y"

def extract_links(pdf_path):
    links = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Extract links using PyMuPDF
        for link in page.get_links():
            if 'uri' in link:
                links.append(link['uri'])
        
        # If OCR is needed
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))

    return links

def get_credentials():
    with open('credentials.json', 'r') as file:
        credentials = json.load(file)
    return credentials

def linkedin_login(email, password , driver):
    driver.get("https://www.linkedin.com/checkpoint/lg/sign-in-another-account")
    
    # Find the username/email field and send the email
    email_field = driver.find_element(By.ID, "username")
    email_field.send_keys(email)
    time.sleep(5)
    
    # Find the password field and send the password
    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys(password)
    time.sleep(5)
    # Submit the form
    password_field.send_keys(Keys.RETURN)
    
    # Wait for a bit to allow login to complete
    time.sleep(15)

def scrape_linkedin_post(url, driver):
    # Open the LinkedIn post URL
    driver.get(url)
    
    # Initialize image_url list
    image_urls = []
    
    try:
        # Wait for all images to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, 'img'))
        )

        # Get all image elements within the post container
        img_elements = driver.find_elements(By.TAG_NAME, 'img')
        
        # Extract URLs from all images
        image_urls = [img.get_attribute('src') for img in img_elements]
        
    except NoSuchElementException:
        image_urls = None
    
    # Wait for the content to load
    try:
        post_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'feed-shared-update-v2__description'))
        )
        post_text = post_content.text.encode('ascii', 'ignore').decode('ascii')
    except:
        post_text = "Could not find the main content of the post."

    return post_text, image_urls

def get_text_chunks_with_metadata(text, source, linkedin_post_url):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=500)
    chunks = text_splitter.split_text(text)
    for i in range(len(chunks)):
        chunks[i] = f"LinkedIn Link: {linkedin_post_url} \n " + chunks[i]

    return [{'content': chunk, 'metadata': {'source': source}} for chunk in chunks]

def get_text_chunks(text, linkedin_post_url):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=500)
    chunks = text_splitter.split_text(text)
    for i in range(len(chunks)):
        chunks[i] = f"LinkedIn Link: {linkedin_post_url} \n " + chunks[i]
    return chunks

def create_faiss_db(chunks, db_name):    
    # Initialize the embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key = GOOGLE_API_KEY)
    
    # Prepare the texts and metadatas
    texts = [chunk['content'] for chunk in chunks]
    metadatas = [chunk['metadata'] for chunk in chunks]
    
    # Create the FAISS index
    vector_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    
    # Save the index locally
    vector_store.save_local(db_name)
    
    print(f"(Yes, this ran, idk why?) FAISS database created and saved as '{db_name}'")
    return vector_store

# I SHOULD add "source" parameter here and make it a common function for all possible source selected! (Check Claude's original code ----> "Filtering FAISS Search Results by Source" Chat)
def user_input(user_question):
    db_name = "FAISS_Index_Lowercase_Trial-Link_Stack-gemini-og"
    prompt_template = """
    You have been given a question and a relevant context. Using the context, explain the answer to the question or discuss the topic given in the question in detail. Never return a blank response.\n
    If the context has anything relevant to the question, you are always supposed to answer something.
    Context:\n{context}?\n
    Question:\n{question}. + Explain in detail.\n
    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0, google_api_key = GOOGLE_API_KEY)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key = GOOGLE_API_KEY)
    new_db1 = FAISS.load_local(db_name, embeddings, allow_dangerous_deserialization=True)

    # Create a filtered retriever based on the source
    filtered_retriever = new_db1.as_retriever(
        search_kwargs={
            'k': 1,
            'filter': lambda x: x['source'] == "LinkedIn"
        }
    )

    # Simple Search, but may not give good results -----> try once
    mq_retriever = MultiQueryRetriever.from_llm(
        retriever=filtered_retriever,
        llm=model
    )

    docs = mq_retriever.invoke(input=user_question.lower())
    print(f"Query = {user_question}\nSource: LinkedIn\nRelevant Documents Extracted:\n")
    print(docs)
    print("\nThis Query has been completed\n==================================================================================")

    #print([doc for doc in docs])
    page_content = docs[0].page_content
    urls = re.findall(r'https?://\S+', page_content)

    image_address = urls[-1] if urls else None
    post_link = urls[0] if urls else None

    response = chain({
        "input_documents": docs,
        "question": user_question
    }, return_only_outputs=True)


    return response, image_address, post_link


def user_input1(user_question):
    db_name = "FAISS_Index_Lowercase_Trial-Link_Stack-gemini-og"
    
    prompt_template = """
    You have been given a question and a relevant context. Using the context, explain the answer to the question or discuss the topic given in the question in detail. Never return a blank response.\n
    If the context has anything relevant to the question, you are always supposed to answer something.
    Context:\n{context}?\n
    Question:\n{question}. + Explain in detail.\n
    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0, google_api_key = GOOGLE_API_KEY)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key = GOOGLE_API_KEY)
    new_db = FAISS.load_local(db_name, embeddings, allow_dangerous_deserialization=True)

    # Create a filtered retriever based on the source
    filtered_retriever = new_db.as_retriever(
        search_kwargs={
            'k': 1,
            'filter': lambda x: x['source'] == "StackExchange"
        }
    )

    mq_retriever = MultiQueryRetriever.from_llm(
        retriever=filtered_retriever,
        llm=model
    )

    docs = mq_retriever.invoke(input=user_question.lower())
    print(f"Query = {user_question}\nSource: Stack Exchange\nRelevant Documents Extracted:\n")
    print(docs)
    print("\nThis Query has been completed\n==================================================================================")

    #print([doc for doc in docs])
    page_content = docs[0].page_content
    urls = re.findall(r'https?://\S+', page_content)

    image_address = urls[-1] if urls else None
    post_link = urls[0] if urls else None

    response = chain({
        "input_documents": docs,
        "question": user_question
    }, return_only_outputs=True)


    return response, image_address, post_link

def user_input2(user_question):
    db_name = "Wiki_DB-gemini-og"
    
    prompt_template = """
    You have been given a question and a relevant context. Using the context, explain the answer to the question or discuss the topic given in the question in detail. Never return a blank response.\n
    If the context has anything relevant to the question, you are always supposed to answer something.
    Context:\n{context}?\n
    Question:\n{question}. + Explain in detail.\n
    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0, google_api_key = GOOGLE_API_KEY)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key = GOOGLE_API_KEY)
    new_db = FAISS.load_local(db_name, embeddings, allow_dangerous_deserialization=True)

    # Create a filtered retriever based on the source
    filtered_retriever = new_db.as_retriever(
        search_kwargs={
            'k': 1,
            'filter': lambda x: x['source'] == "Wiki"
        }
    )

    mq_retriever = MultiQueryRetriever.from_llm(
        retriever=filtered_retriever,
        llm=model
    )

    docs = mq_retriever.invoke(input=user_question.lower())
    print(f"Query = {user_question}\nSource: Wiki\nRelevant Documents Extracted:\n")
    print(docs)
    print("\nThis Query has been completed\n==================================================================================")

    #print([doc for doc in docs])
    page_content = docs[0].page_content
    urls = re.findall(r'https?://\S+', page_content)

    image_address = urls[-1] if urls else None
    post_link = urls[0] if urls else None

    response = chain({
        "input_documents": docs,
        "question": user_question
    }, return_only_outputs=True)


    return response, image_address, post_link


#all_chunks = []

#links = extract_links('List of my best posts -2021.pdf') + extract_links('List of my best posts 2022.pdf') + extract_links('List of my best posts 2023.pdf')
#print(f"# links: {len(links)}\n==============================================")
#driver = webdriver.Chrome()

#credentials = get_credentials()
#if credentials:
#    linkedin_email = credentials.get('email')
#    linkedin_password = credentials.get('password')

# Log in to LinkedIn
#linkedin_login(linkedin_email, linkedin_password , driver)

#for linkedin_post_url in links:
#    post_text,image_address = scrape_linkedin_post(linkedin_post_url , driver)
#    text_chunks = get_text_chunks_with_metadata(post_text, "LinkedIn", linkedin_post_url)
#    for chunk in text_chunks:
#        all_chunks.append(chunk)

# Writing to a file
#with open('all_chunks.json', 'w') as file:
#    json.dump(all_chunks, file, indent=2)
# Reading from the file and recreating the list
#with open('all_chunks.json', 'r') as file:
#    all_chunks = json.load(file)

#print("Data has been read from all_chunks.txt to the variable all_chunks")
#print(all_chunks)
#create_faiss_db(all_chunks)

#print(f"\n\n\n\n\n\n\n\n\n\nThe length of all_chunks is: {len(all_chunks)} | The # links was: {len(links)}")
print("=============================================DONE=========================================")