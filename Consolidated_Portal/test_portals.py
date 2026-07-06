#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite for Consolidated AI Portal
Tests all 10 AI portals with dedicated test cases
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:9999"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_test(name, passed, error=None):
    status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if passed else f"{Colors.RED}✗ FAILED{Colors.END}"
    print(f"  {status} | {name}")
    if error:
        print(f"    {Colors.RED}Error: {error}{Colors.END}")

def test_server_connectivity():
    """Test if server is running"""
    print_header("SERVER CONNECTIVITY TEST")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        passed = response.status_code == 200
        print_test("Server is running", passed)
        return passed
    except Exception as e:
        print_test("Server is running", False, str(e))
        return False

def test_default_check():
    """Test default greeting endpoint"""
    print_header("DEFAULT HEALTH CHECK TEST")
    try:
        response = requests.get(f"{BASE_URL}/api/default", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            passed = "message" in data and "Ollama" in data.get("message", "")
            print_test("Default check returns proper greeting", passed)
            return passed
        else:
            print_test("Default check returns proper greeting", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Default check returns proper greeting", False, str(e))
        return False

def test_endpoints_list():
    """Test endpoints listing"""
    print_header("AVAILABLE ENDPOINTS TEST")
    try:
        response = requests.get(f"{BASE_URL}/api/endpoints", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  {Colors.CYAN}Total Endpoints: {data.get('total_endpoints', 0)}{Colors.END}")
            endpoints = data.get('endpoints', [])
            for ep in endpoints:
                print(f"    • {ep.get('name')} ({ep.get('model')})")
            passed = len(endpoints) == 10
            print_test(f"All {len(endpoints)}/10 endpoints listed", passed)
            return True
        else:
            print_test("Endpoints endpoint working", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Endpoints endpoint working", False, str(e))
        return False

def test_ollama_status():
    """Test Ollama connection status"""
    print_header("OLLAMA SERVICE STATUS TEST")
    try:
        response = requests.get(f"{BASE_URL}/api/ollama-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            available = data.get('available', False)
            status_text = f"{Colors.GREEN}✓ Connected{Colors.END}" if available else f"{Colors.RED}✗ Unavailable{Colors.END}"
            print(f"  Ollama Status: {status_text}")
            if available:
                models_count = data.get('models_count', 0)
                print(f"  Models Loaded: {models_count}")
            print_test("Ollama service connectivity", available)
            return available
        else:
            print_test("Ollama service connectivity", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Ollama service connectivity", False, str(e))
        return False

def test_code_assistant():
    """Test AI Code Assistant Portal"""
    print_header("TEST 1: AI CODE ASSISTANT")
    try:
        payload = {
            "prompt": "Python function to add two numbers",
            "mode": "generate"
        }
        response = requests.post(f"{BASE_URL}/api/generate_code", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Code Assistant generates code", passed)
            return passed
        else:
            print_test("Code Assistant generates code", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Code Assistant generates code", False, str(e))
        return False

def test_content_writer():
    """Test AI Content Writer Portal"""
    print_header("TEST 2: AI CONTENT WRITER")
    try:
        payload = {
            "topic": "Artificial Intelligence in Healthcare",
            "style": "technical"
        }
        response = requests.post(f"{BASE_URL}/api/generate_content", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Content Writer generates content", passed)
            return passed
        else:
            print_test("Content Writer generates content", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Content Writer generates content", False, str(e))
        return False

def test_legal_analyzer():
    """Test AI Legal Analyzer Portal"""
    print_header("TEST 3: AI LEGAL ANALYZER")
    try:
        payload = {
            "text": "This agreement is entered into between Party A and Party B for the purpose of collaboration on software development projects."
        }
        response = requests.post(f"{BASE_URL}/api/analyze_legal_text", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Legal Analyzer analyzes documents", passed)
            return passed
        else:
            print_test("Legal Analyzer analyzes documents", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Legal Analyzer analyzes documents", False, str(e))
        return False

def test_news_summarizer():
    """Test AI News Summarizer Portal"""
    print_header("TEST 4: AI NEWS SUMMARIZER")
    try:
        response = requests.get(f"{BASE_URL}/api/fetch_and_summarize_news?category=technology", timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "summary" in data
            if passed:
                print(f"  {Colors.CYAN}Summary (first 200 chars):{Colors.END}")
                print(f"  {data['summary'][:200]}...")
            print_test("News Summarizer fetches and summarizes", passed)
            return passed
        elif response.status_code == 503:
            print_test("News Summarizer fetches and summarizes", False, "Ollama not available")
            return False
        else:
            print_test("News Summarizer fetches and summarizes", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("News Summarizer fetches and summarizes", False, str(e))
        return False

def test_proofreader():
    """Test AI Proofreader Portal"""
    print_header("TEST 5: AI PROOFREADER")
    try:
        payload = {
            "text": "Their is a spelling eror in this sentance. It shoud be corrected."
        }
        response = requests.post(f"{BASE_URL}/api/proofread", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Proofreader corrects text", passed)
            return passed
        else:
            print_test("Proofreader corrects text", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Proofreader corrects text", False, str(e))
        return False

def test_text_summarizer():
    """Test AI Text Summarizer Portal"""
    print_header("TEST 6: AI TEXT SUMMARIZER")
    try:
        payload = {
            "text": "Artificial Intelligence has revolutionized many industries. Machine learning algorithms can now process vast amounts of data and identify patterns that would be impossible for humans to detect manually. Deep learning has enabled breakthrough applications in computer vision, natural language processing, and autonomous systems."
        }
        response = requests.post(f"{BASE_URL}/api/summarize", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Text Summarizer summarizes text", passed)
            return passed
        else:
            print_test("Text Summarizer summarizes text", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Text Summarizer summarizes text", False, str(e))
        return False

def test_virtual_assistant():
    """Test AI Virtual Assistant Portal"""
    print_header("TEST 7: AI VIRTUAL ASSISTANT")
    try:
        payload = {
            "user_query": "What is the capital of France?"
        }
        response = requests.post(f"{BASE_URL}/api/virtual_assistant", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Virtual Assistant answers queries", passed)
            return passed
        else:
            print_test("Virtual Assistant answers queries", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Virtual Assistant answers queries", False, str(e))
        return False

def test_customer_support():
    """Test Customer Support Chatbot Portal"""
    print_header("TEST 8: CUSTOMER SUPPORT CHATBOT")
    try:
        payload = {
            "user_query": "How do I reset my password?"
        }
        response = requests.post(f"{BASE_URL}/api/customer_support", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Customer Support responds to queries", passed)
            return passed
        else:
            print_test("Customer Support responds to queries", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Customer Support responds to queries", False, str(e))
        return False

def test_shop_recommender():
    """Test eCommerce AI Recommender Portal"""
    print_header("TEST 9: eCOMMERCE AI RECOMMENDER")
    try:
        payload = {
            "preferences": "I like running shoes, athletic wear, and fitness accessories under $100"
        }
        response = requests.post(f"{BASE_URL}/api/ecommerce_recommender", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Shop Recommender provides recommendations", passed)
            return passed
        else:
            print_test("Shop Recommender provides recommendations", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Shop Recommender provides recommendations", False, str(e))
        return False

def test_symptom_checker():
    """Test Medical AI Symptom Checker Portal"""
    print_header("TEST 10: MEDICAL AI SYMPTOM CHECKER")
    try:
        payload = {
            "symptoms": "fever, cough, fatigue, sore throat"
        }
        response = requests.post(f"{BASE_URL}/api/medical_symptom_checker", data=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            passed = "response" in data and len(data.get("response", "")) > 0
            if passed:
                print(f"  {Colors.CYAN}Response (first 200 chars):{Colors.END}")
                print(f"  {data['response'][:200]}...")
            print_test("Symptom Checker analyzes symptoms", passed)
            return passed
        else:
            print_test("Symptom Checker analyzes symptoms", False, f"Status {response.status_code}")
            return False
    except Exception as e:
        print_test("Symptom Checker analyzes symptoms", False, str(e))
        return False

def run_all_tests():
    """Run all tests and generate report"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print(r"""
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                 CONSOLIDATED AI PORTAL TEST SUITE v1.0                    ║
    ║                   Comprehensive Automated Test Report                     ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    print(f"{Colors.END}")
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}\n")
    
    # Run all tests
    tests = [
        ("Server Connectivity", test_server_connectivity),
        ("Default Check", test_default_check),
        ("Endpoints List", test_endpoints_list),
        ("Ollama Status", test_ollama_status),
        ("Code Assistant", test_code_assistant),
        ("Content Writer", test_content_writer),
        ("Legal Analyzer", test_legal_analyzer),
        ("News Summarizer", test_news_summarizer),
        ("Proofreader", test_proofreader),
        ("Text Summarizer", test_text_summarizer),
        ("Virtual Assistant", test_virtual_assistant),
        ("Customer Support", test_customer_support),
        ("Shop Recommender", test_shop_recommender),
        ("Symptom Checker", test_symptom_checker),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)  # Small delay between tests
    
    # Generate summary report
    print_header("TEST SUMMARY REPORT")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"{Colors.CYAN}Test Results:{Colors.END}")
    for test_name, result in results:
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if result else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"  {status} | {test_name}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed ({int(passed/total*100)}%){Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! Portal is fully operational.{Colors.END}")
    elif passed >= total * 0.8:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  {total - passed} test(s) failed. Please review.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Multiple test failures detected. Review required.{Colors.END}")
    
    print(f"\nTest Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    run_all_tests()
