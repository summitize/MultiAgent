import requests
import json

print('=== TESTING BACKWARD COMPATIBILITY ===\n')

# Test old endpoints
endpoints = [
    ('/api/generate_code', {'prompt': 'write a hello world function'}),
    ('/api/generate_content', {'prompt': 'Write about Python'}),
    ('/api/analyze_legal_text', {'text': 'sample contract clause'}),
]

for endpoint, payload in endpoints:
    try:
        response = requests.post(f'http://localhost:8080{endpoint}', data=payload, timeout=5)
        if response.status_code == 200:
            print(f'✓ {endpoint} - Working')
        else:
            print(f'✗ {endpoint} - HTTP {response.status_code}')
    except Exception as e:
        print(f'✗ {endpoint} - {str(e)[:50]}')

print('\n=== TESTING DYNAMIC FORM FIELD GENERATION ===\n')

# Get agents and check systemPrompt parsing
response = requests.get('http://localhost:8080/api/agents')
agents = response.json()['agents']

for agent in agents[:3]:
    print(f'Agent: {agent["name"]}')
    print(f'  systemPrompt: {agent["systemPrompt"][:60]}...')
    # Extract variables from systemPrompt
    import re
    variables = set(re.findall(r'\{([^}]+)\}', agent['systemPrompt']))
    print(f'  Form fields (from {variables}): {variables}')
    print()
