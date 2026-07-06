#!/usr/bin/env python3
"""
Comprehensive test suite for Consolidated_Portal app.py
Tests all API endpoints for basic functionality
"""

import requests
import sys
import time
from urllib.parse import urljoin

BASE_URL = "http://localhost:8080"
TIMEOUT = 5  # seconds

def test_endpoint(method, path, data=None, params=None, description=""):
    """Test a single endpoint"""
    url = urljoin(BASE_URL, path)
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, data=data, timeout=TIMEOUT)
        else:
            return {"status": "SKIP", "reason": f"Unknown method: {method}"}
        
        status_code = response.status_code
        is_success = 200 <= status_code < 300
        
        try:
            json_data = response.json()
            response_preview = str(json_data)[:80]
        except:
            response_preview = response.text[:80]
        
        return {
            "status": "PASS" if is_success else "FAIL",
            "code": status_code,
            "response": response_preview,
            "method": method,
            "path": path,
            "description": description
        }
    except requests.exceptions.Timeout:
        return {
            "status": "TIMEOUT",
            "code": 0,
            "response": "Request timed out (Ollama likely not responding)",
            "method": method,
            "path": path,
            "description": description
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "UNREACHABLE",
            "code": 0,
            "response": f"Cannot connect to server: {str(e)[:50]}",
            "method": method,
            "path": path,
            "description": description
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "code": 0,
            "response": str(e)[:80],
            "method": method,
            "path": path,
            "description": description
        }

def main():
    print("=" * 120)
    print("Consolidated Portal - API Test Suite")
    print("=" * 120)
    print()
    
    # Test infrastructure endpoints first (non-LLM)
    tests = [
        # === Infrastructure Tests ===
        ("GET", "/", None, None, "Home page (serves index.html)"),
        ("GET", "/api/health", None, None, "Health check endpoint"),
        ("GET", "/api/default", None, None, "Default greeting endpoint"),
        ("GET", "/api/agents", None, None, "List all available agents"),
        ("GET", "/api/endpoints", None, None, "List all endpoints (backward compat)"),
        ("GET", "/api/ollama-status", None, None, "Check Ollama service status"),
        
        # === Agent Endpoints (these may timeout if Ollama is down) ===
        ("POST", "/api/generate_code", {"prompt": "print hello", "mode": "generate"}, None, "Code generation endpoint"),
        ("POST", "/api/summarize", {"text": "FastAPI is a modern web framework"}, None, "Text summarization"),
        ("POST", "/api/proofread", {"text": "ths is a testt"}, None, "Text proofreading"),
        ("POST", "/api/generate_content", {"topic": "AI", "style": "professional"}, None, "Content generation"),
        ("POST", "/api/virtual_assistant", {"user_query": "Hello"}, None, "Virtual assistant"),
        ("POST", "/api/customer_support", {"user_query": "Help"}, None, "Customer support"),
        ("POST", "/api/analyze_legal_text", {"text": "Sample contract text"}, None, "Legal analysis"),
        ("POST", "/api/ecommerce_recommender", {"preferences": "laptop"}, None, "Product recommendations"),
        ("POST", "/api/medical_symptom_checker", {"symptoms": "fever"}, None, "Symptom checker"),
        ("GET", "/api/fetch_and_summarize_news", None, {"category": "technology"}, "News summarization"),
    ]
    
    results = []
    for method, path, data, params, description in tests:
        result = test_endpoint(method, path, data, params, description)
        results.append(result)
    
    # Print results
    print(f"{'Status':<12} {'HTTP':<5} {'Method':<6} {'Endpoint':<35} Description")
    print("-" * 120)
    
    for result in results:
        status = result["status"]
        code = result["code"]
        method = result["method"]
        path = result["path"]
        desc = result["description"]
        
        # Symbol
        if status == "PASS":
            symbol = "✓"
        elif status == "FAIL":
            symbol = "✗"
        elif status == "TIMEOUT":
            symbol = "⏱"
        else:
            symbol = "!"
        
        print(f"{symbol} {status:<11} {code:<5} {method:<6} {path:<35} {desc}")
    
    # Summary
    print()
    print("=" * 120)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
    errors = sum(1 for r in results if r["status"] in ["ERROR", "UNREACHABLE"])
    
    print(f"Summary: {len(results)} tests | ✓ {passed} passed | ✗ {failed} failed | ⏱ {timeout} timeout | ! {errors} errors")
    print()
    
    if timeout > 0:
        print("⚠️  Note: Timeouts likely indicate Ollama service is not running.")
        print("   Start Ollama with: ollama serve")
        print()
    
    if errors > 0:
        print(f"❌ Cannot reach server at {BASE_URL}")
        print("   Is the app running? Start with: py -m uvicorn app:app --host 0.0.0.0 --port 8080")
        return 1
    
    if failed > 0:
        return 1
    
    print("✓ All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
