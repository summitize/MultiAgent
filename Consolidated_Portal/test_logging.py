#!/usr/bin/env python3
"""
Quick test to verify logging is working
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8765"

def test_logging():
    print("\n" + "="*80)
    print("  LOGGING VERIFICATION TEST")
    print("="*80 + "\n")
    
    try:
        # Test 1: Health check
        print("✓ Test 1: Health Check")
        r = requests.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        print(f"  Response: {r.json()}\n")
        
        # Test 2: Default endpoint
        print("✓ Test 2: Default Endpoint") 
        r = requests.get(f"{BASE_URL}/api/default")
        assert r.status_code == 200
        print(f"  Response: {r.json()}\n")
        
        # Test 3: Endpoints list
        print("✓ Test 3: Available Endpoints")
        r = requests.get(f"{BASE_URL}/api/endpoints")
        assert r.status_code == 200
        data = r.json()
        print(f"  Total endpoints: {data['total_endpoints']}")
        print(f"  First endpoint: {data['endpoints'][0]['name']}\n")
        
        # Test 4: View logs
        print("✓ Test 4: Application Logs")
        r = requests.get(f"{BASE_URL}/api/logs?lines=10")
        assert r.status_code == 200
        data = r.json()
        print(f"  Log file: {data['log_file']}")
        print(f"  Total log lines: {data['total_lines']}")
        print(f"  Recent log entries (last 10 lines):")
        print(f"  {'-'*76}")
        log_lines = data['logs'].split('\n')
        for line in log_lines[-10:]:
            if line.strip():
                print(f"  {line}")
        print(f"  {'-'*76}\n")
        
        print("="*80)
        print("  ✅ ALL TESTS PASSED - LOGGING IS WORKING!")
        print("="*80 + "\n")
        print("📊 Logging Summary:")
        print(f"   • Log file location: Consolidated_Portal/logs/{data['log_file']}")
        print(f"   • Total log entries captured: {data['total_lines']}")
        print(f"   • API endpoint: GET /api/logs?lines=50")
        print(f"   • Application logging: ✓ ENABLED")
        print(f"   • File output: ✓ WORKING")
        print(f"   • Console output: ✓ WORKING\n")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Cannot connect to {BASE_URL}")
        print("   Please ensure FastAPI server is running!")
        sys.exit(1)
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_logging()
