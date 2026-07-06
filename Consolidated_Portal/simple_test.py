#!/usr/bin/env python3
"""
Direct test execution - writes results to test_results.txt
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8080"
TIMEOUT = 5
OUTPUT_FILE = "test_results.txt"

results = []
output = []

def log(msg):
    output.append(msg)
    print(msg)

def test_endpoint(method, path, data=None, params=None, description=""):
    """Test a single endpoint"""
    url = BASE_URL + path if path.startswith("/") else BASE_URL + "/" + path
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=TIMEOUT)
        else:
            response = requests.post(url, data=data, timeout=TIMEOUT)
        
        is_success = 200 <= response.status_code < 300
        try:
            json_data = response.json()
            resp_text = json.dumps(json_data)[:100]
        except:
            resp_text = response.text[:100]
        
        return {
            "status": "PASS" if is_success else "FAIL",
            "code": response.status_code,
            "response": resp_text,
            "method": method,
            "path": path,
            "description": description
        }
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "code": 0, "response": "Timeout", "method": method, "path": path, "description": description}
    except requests.exceptions.ConnectionError:
        return {"status": "UNREACHABLE", "code": 0, "response": "Cannot connect", "method": method, "path": path, "description": description}
    except Exception as e:
        return {"status": "ERROR", "code": 0, "response": str(e)[:50], "method": method, "path": path, "description": description}

log("="*120)
log("Consolidated Portal - app.py Test Results")
log(f"Timestamp: {datetime.now().isoformat()}")
log("="*120)
log("")

# Run tests
tests = [
    ("GET", "/", None, None, "Home page"),
    ("GET", "/api/health", None, None, "Health check"),
    ("GET", "/api/default", None, None, "Default endpoint"),
    ("GET", "/api/agents", None, None, "List agents"),
    ("GET", "/api/endpoints", None, None, "List endpoints (backward compat)"),
    ("GET", "/api/ollama-status", None, None, "Check Ollama status"),
]

for method, path, data, params, description in tests:
    result = test_endpoint(method, path, data, params, description)
    results.append(result)

# Print results
log(f"{'Status':<12} {'Code':<5} {'Method':<6} {'Endpoint':<30} {'Description':<30}")
log("-"*120)

for r in results:
    status = r["status"]
    code = r["code"]
    method = r["method"]
    path = r["path"]
    desc = r["description"]
    print(f"{status:<12} {code:<5} {method:<6} {path:<30} {desc:<30}")

# Summary
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
errors = sum(1 for r in results if r["status"] in ["ERROR", "UNREACHABLE"])

log("")
log("="*120)
log(f"Summary: {len(results)} tests | {passed} passed | {failed} failed | {timeout} timeout | {errors} errors")
log("="*120)

# Write to file
with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(output))

print(f"\nResults saved to: {OUTPUT_FILE}")
