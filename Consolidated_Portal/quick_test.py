#!/usr/bin/env python3
"""Quick test of the AI Portal endpoints"""

import requests
import json

BASE_URL = "http://localhost:9999"

def test():
    print("\n" + "="*80)
    print(" QUICK API TEST - AI Portal Endpoints")
    print("="*80 + "\n")
    
    # Test 1: Default endpoint
    print("1. Testing /api/default endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/api/default", timeout=5)
        if r.status_code == 200:
            print(f"   ✓ Status: {r.status_code}")
            print(f"   Response: {r.json()}")
        else:
            print(f"   ✗ Status: {r.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Endpoints list
    print("\n2. Testing /api/endpoints endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/api/endpoints", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✓ Status: {r.status_code}")
            print(f"   Total Endpoints: {data.get('total_endpoints', 0)}")
            print("   Available Endpoints:")
            for ep in data.get('endpoints', []):
                print(f"     - {ep['name']} ({ep['method']} {ep['endpoint']})")
        else:
            print(f"   ✗ Status: {r.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Ollama status
    print("\n3. Testing /api/ollama-status endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/api/ollama-status", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✓ Status: {r.status_code}")
            print(f"   Ollama Available: {data.get('available', False)}")
            if data.get('available'):
                print(f"   Models Loaded: {data.get('models_count', 0)}")
        else:
            print(f"   ✗ Status: {r.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Sample tool - Code Assistant
    print("\n4. Testing /api/generate_code endpoint...")
    try:
        payload = {"prompt": "Python function to add two numbers", "mode": "generate"}
        r = requests.post(f"{BASE_URL}/api/generate_code", data=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            print(f"   ✓ Status: {r.status_code}")
            response_text = data.get('response', '')
            if response_text:
                print(f"   Response preview: {response_text[:100]}...")
            else:
                print(f"   Response: {data}")
        else:
            print(f"   ✗ Status: {r.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test()
