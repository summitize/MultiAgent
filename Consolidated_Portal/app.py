from fastapi import FastAPI, HTTPException, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
from datetime import datetime

app = FastAPI(title="Consolidated Multi-Agent Portal")

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mapping
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration from environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
# Ensure HTTP protocol (not HTTPS for local Ollama)
if OLLAMA_BASE_URL.startswith("https://"):
    OLLAMA_BASE_URL = OLLAMA_BASE_URL.replace("https://", "http://", 1)
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"
NEWS_API_URL = "https://newsapi.org/v2/top-headlines"
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "NEWS_API_KEY")  # Replace with actual API key if available

# Track Ollama status
ollama_status = {"available": True, "last_check": None, "error": None}

@app.get("/")
def serve_homepage():
    """ Serve the index.html file when accessing the root URL """
    return FileResponse(os.path.join("static", "index.html"))

@app.get("/api/health")
def health_check():
    """ Health check endpoint """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/ollama-status")
def check_ollama_status():
    """ Check if Ollama is available """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_status["available"] = True
            ollama_status["error"] = None
            ollama_status["last_check"] = datetime.now().isoformat()
            models = response.json().get("models", [])
            return {"available": True, "models_count": len(models), "models": [m.get("name") for m in models]}
        else:
            ollama_status["available"] = False
            ollama_status["error"] = f"HTTP {response.status_code}"
            return {"available": False, "error": f"Ollama returned HTTP {response.status_code}"}
    except requests.exceptions.Timeout:
        ollama_status["available"] = False
        ollama_status["error"] = "Connection timeout"
        return {"available": False, "error": "Ollama connection timeout. Service may be down."}
    except requests.exceptions.ConnectionError:
        ollama_status["available"] = False
        ollama_status["error"] = "Connection refused"
        return {"available": False, "error": "Cannot connect to Ollama. Is it running locally?"}
    except Exception as e:
        ollama_status["available"] = False
        ollama_status["error"] = str(e)
        return {"available": False, "error": f"Ollama check failed: {str(e)}"}

# 1. AI Code Assistant
@app.post("/api/generate_code")
def generate_code(prompt: str = Form(...), mode: str = Form(...)):
    if mode == "generate":
        full_prompt = f"Write a clean, well-documented {prompt} code snippet."
    elif mode == "debug":
        full_prompt = f"Debug and fix the following code:\n{prompt}"
    else:
        raise HTTPException(status_code=400, detail="Invalid mode selected.")
    return call_ollama("qwen2.5-coder:7b", full_prompt)

# 2. AI Content Writer
@app.post("/api/generate_content")
def generate_content(topic: str = Form(...), style: str = Form(...)):
    prompt = f"Write a detailed blog post about '{topic}' in a {style} tone."
    return call_ollama("gemma4:latest", prompt)

# 3. AI Legal Analyzer
@app.post("/api/analyze_legal_text")
def analyze_legal_text(text: str = Form(...)):
    prompt = f"Extract key insights from the following legal document:\n{text}\nSummarize important clauses, risks, and obligations."
    return call_ollama("phi3:14b", prompt)

# 4. AI News Summarizer
@app.get("/api/fetch_and_summarize_news")
def fetch_and_summarize_news(category: str = Query("technology")):
    headers = {"Authorization": f"Bearer {NEWS_API_KEY}"}
    params = {"category": category, "language": "en", "apiKey": NEWS_API_KEY}
    try:
        news_response = requests.get(NEWS_API_URL, params=params, headers=headers)
        if news_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch news articles")
        news_data = news_response.json()
        if "articles" not in news_data or not news_data["articles"]:
            return {"summary": "No news articles found for this category."}
        
        articles = news_data["articles"][:3]
        news_text = "\n".join([f"- {article['title']} ({article['source']['name']})" for article in articles])
        
        # Call ollama
        ollama_res = call_ollama("qwen3.6:27b", f"Summarize these news headlines:\n{news_text}")
        return {"summary": ollama_res.get("response", "No summary available."), "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch or summarize news: {str(e)}")

# 5. AI Proofreader
@app.post("/api/proofread")
def proofread_text(text: str = Form(...)):
    prompt = f"Correct the grammar, spelling, and sentence structure of the following text:\n{text}"
    return call_ollama("DeepSeek-R1:latest", prompt)

# 6. AI Text Summarizer
@app.post("/api/summarize")
def summarize_text(text: str = Form(...)):
    prompt = f"Summarize this: {text}"
    return call_ollama("mistral:7b", prompt)

# 7. AI Virtual Assistant
@app.post("/api/virtual_assistant")
def virtual_assistant(user_query: str = Form(...)):
    prompt = f"You are an AI-powered virtual assistant that helps with task scheduling and answering queries.\nUser: {user_query}\nAI:"
    return call_ollama("gemma4:latest", prompt)

# 8. Customer Support Chatbot
@app.post("/api/customer_support")
def customer_support(user_query: str = Form(...)):
    prompt = f"You are a customer support chatbot. Answer the user's question professionally and concisely.\nUser: {user_query}\nChatbot:"
    return call_ollama("qwen3.6:27b", prompt)

# 9. eCommerce AI Recommender
@app.post("/api/ecommerce_recommender")
def ecommerce_recommender(preferences: str = Form(...)):
    prompt = f"You are an AI product recommender. Based on the user's preferences, suggest the best matching products.\nUser Preferences: {preferences}\nRecommendations:"
    return call_ollama("granite4.1:8b", prompt)

# 10. Medical AI Symptom Checker
@app.post("/api/medical_symptom_checker")
def medical_symptom_checker(symptoms: str = Form(...)):
    prompt = f"You are a medical AI assistant trained to analyze symptoms. Based on the provided symptoms, give possible explanations and general advice. Do not provide a diagnosis or replace a doctor's consultation.\nUser Symptoms: {symptoms}\nMedical AI:"
    return call_ollama("phi3:14b", prompt)


# Helper function
def call_ollama(model_name: str, prompt: str):
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model_name, "prompt": prompt, "stream": False},
            headers=headers,
            timeout=300  # 5 min timeout for inference
        )
        response_data = response.text.strip()
        try:
            json_response = json.loads(response_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail=f"Invalid JSON response from Ollama: {response_data}")
        return {"response": json_response.get("response", "No valid response received.")}
    except requests.exceptions.Timeout:
        ollama_status["available"] = False
        raise HTTPException(status_code=503, detail="⚠️ Ollama is not responding. The service may be offline or overloaded. Please try again later.")
    except requests.exceptions.ConnectionError:
        ollama_status["available"] = False
        raise HTTPException(status_code=503, detail="⚠️ Cannot connect to Ollama. Please ensure the local Ollama service is running on " + OLLAMA_BASE_URL)
    except requests.exceptions.RequestException as e:
        ollama_status["available"] = False
        raise HTTPException(status_code=503, detail=f"⚠️ Ollama request failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Using 8080 to avoid conflicts with 8000
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
