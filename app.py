# from flask import Flask, render_template, request, jsonify
# import requests

# app = Flask(__name__)

# # Your Tomorrow.io API key
# API_KEY = 'nNDIlAx6usL8MSqQ3UHwpqR2jJY0CjyR'  # Replace with your actual API key

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/get_weather', methods=['GET'])
# def get_weather():
#     city = request.args.get('city')  # Get the city name from the query parameter

#     if not city:
#         return jsonify({"error": "City is required"}), 400

#     # Make an API request to Tomorrow.io (Climacell)
#     url = f'https://api.tomorrow.io/v4/timelines'
#     params = {
#         'location': city,  # Can be a city name or latitude,longitude
#         'fields': 'temperature,precipitationProbability',
#         'apikey': API_KEY,
#         'timesteps': 'current',
#     }

#     response = requests.get(url, params=params)

#     if response.status_code == 200:
#         data = response.json()
#         temperature = data['data']['timelines'][0]['intervals'][0]['values']['temperature']
#         precipitation = data['data']['timelines'][0]['intervals'][0]['values']['precipitationProbability']
        
#         # Return weather data as JSON
#         return jsonify({
#             'temperature': f'{temperature}°C',
#             'precipitation': f'{precipitation}%'
#         })
#     else:
#         return jsonify({"error": "Unable to fetch weather data"}), 500

# if __name__ == '__main__':
#     app.run(debug=True)









from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import chromadb
from chromadb.config import Settings
import chromadb.utils.embedding_functions as embedding_functions
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os














from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Add your OpenWeather API key here
API_KEY = ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_forecast', methods=['POST'])
def get_forecast():
    city = request.form.get('city')
    if not city:
        return jsonify({"error": "City is required"}), 400
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={key}fcb86&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            return jsonify({"error": data.get("message", "An error occurred")}), 400

        # Extract relevant forecast data
        forecast = [
            {
                "date": item["dt_txt"],
                "temp": item["main"]["temp"],
                "description": item["weather"][0]["description"]
            }
            for item in data["list"]
        ]
        return jsonify({"city": data["city"]["name"], "forecast": forecast})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

























index_path = "/teamspace/studios/this_studio/aman"

try:
    # Initialize ChromaDB with the path to the existing index
    client = chromadb.PersistentClient(path=index_path)
    google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key="AIzaSyAeFt00isxX2ViHXSlBxhPPO4LSS9PoRhg")

    collection_name = "weather"
    weather_collection = client.get_or_create_collection(name = "weather", metadata={"hnsw:space": "cosine"}, embedding_function=google_ef)
    
except Exception as e:
    print(f"Error initializing ChromaDB: {e}")

@app.route('/')
def base():
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
            """You are a doctor with 25 years of experience in medical fields, your task is to give accurate response to the patient query. \
            I am also providing you patients' question and answer of previous doctors and patients with their doctor’s suggestions when they \
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
    app.run(debug=True, port=5002)

