from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import chromadb
from chromadb.config import Settings
import chromadb.utils.embedding_functions as embedding_functions
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os


app = Flask(__name__)
CORS(app, resources={r"/query": {"origins": "*"}})


# Path to the directory where the index is stored
index_path = "/teamspace/studios/this_studio/aman"

try:
    # Initialize ChromaDB with the path to the existing index
    client = chromadb.PersistentClient(path=index_path)
    google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key="")

    collection_name = "weather"
    weather_collection = client.get_or_create_collection(name = "weather", metadata={"hnsw:space": "cosine"}, embedding_function=google_ef)
    
except Exception as e:
    print(f"Error initializing ChromaDB: {e}")

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/query', methods=['POST'])
def query():
    try:
        patient_query = request.json.get('query')
        if not patient_query:
            return jsonify({"error": "No query provided"}), 400
        
        # Query the collection using patient_query
        results = weather_collection.query(query_texts=[patient_query], n_results=2)  # Retrieve 2 relevant results
        conversations = [{'Weather_dec': i['Weather_dec'], 'Safety Measures': i['Safety Measures'], 'Weather': i['Weather']} for i in results['metadatas'][0]]

        # LLM call
        llm = ChatGoogleGenerativeAI(model="gemini-pro")
        prompt_template = PromptTemplate.from_template(
            """You are a weather expert with 25 years of experience in climate fields, your task is to give accurate response to the  query. \
            I am also providing you user' question and answer of previous expert and patients with their expert’s suggestions when they \
            had similar problems, so you can also use this content. Provide a response as normal text.
            
            Patient Query : {patient_question}
            
            Other_Patients_Conversation : {conversations}
            """
        )
        pipeline = prompt_template | llm
        
        response = pipeline.invoke({"patient_question": patient_query, "conversations": conversations})

        return jsonify({"response": response.content, "conversations": conversations})
    except Exception as e:
        print(f"Error during querying: {e}")
        return jsonify({"error": str(e)}), 500

          

if __name__ == '__main__':
    app.run(debug=True, port=8501)



