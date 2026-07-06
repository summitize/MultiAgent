# Consolidated Multi-Agent AI Portal

A FastAPI-based web application that provides 10 different AI tools powered by Ollama local models.

## Features

- 🤖 **AI Code Assistant** - Code generation and debugging
- ✍️ **Content Writer** - Blog and article generation
- ⚖️ **Legal Analyzer** - Legal document analysis
- 📰 **News Summarizer** - News aggregation and summarization
- ✅ **Proofreader** - Grammar and spelling correction
- 📝 **Text Summarizer** - Content condensing
- 🤖 **Virtual Assistant** - Task scheduling and Q&A
- 💬 **Customer Support Chatbot** - Support responses
- 🛒 **E-commerce Recommender** - Product recommendations
- 🏥 **Medical Symptom Checker** - Symptom analysis

## Deployment to Azure

### Prerequisites

- Azure subscription
- Azure CLI (`az`) installed
- Custom domain configured (e.g., ai-playground.summitize.in)

### Deployment Steps

1. **Deploy to Azure App Service:**
   ```bash
   python -m pip install -r requirements.txt
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```

2. **Environment Variables (on Azure App Service):**
   - `OLLAMA_BASE_URL`: Set to your local Ollama URL (e.g., `http://localhost:11434`)
   - `NEWS_API_KEY`: Your NewsAPI key (optional)

3. **Configure Custom Domain:**
   - Point DNS to your App Service
   - Configure SSL certificate
   - Update CORS if needed

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Ensure Ollama is running
ollama serve

# Start the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Ollama Status

The application automatically checks Ollama availability:
- ✅ If Ollama is running, all AI features are available
- ⚠️ If Ollama is offline, a banner appears indicating the service is unavailable

### API Endpoints

- `GET /` - Main portal page
- `GET /api/health` - Health check
- `GET /api/ollama-status` - Check Ollama service status
- `POST /api/generate_code` - AI Code Assistant
- `POST /api/generate_content` - Content Writer
- `POST /api/analyze_legal_text` - Legal Analyzer
- `GET /api/fetch_and_summarize_news` - News Summarizer
- `POST /api/proofread` - Proofreader
- `POST /api/summarize` - Text Summarizer
- `POST /api/virtual_assistant` - Virtual Assistant
- `POST /api/customer_support` - Customer Support
- `POST /api/ecommerce_recommender` - E-commerce Recommender
- `POST /api/medical_symptom_checker` - Medical Symptom Checker
