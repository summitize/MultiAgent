import requests
import json

# Test /api/agents endpoint
response = requests.get('http://localhost:8080/api/agents')
data = response.json()

print('=== AGENT API TEST ===')
print(f'Total agents: {data["total_agents"]}')
print(f'\nFirst 3 agents:')
for agent in data['agents'][:3]:
    print(f'  - {agent["name"]} ({agent["id"]})')
    print(f'    Category: {agent["category"]}, Icon: {agent["icon"]}')
    print(f'    Models: {agent["supportedModels"]}')
    print(f'    Suggested prompts: {len(agent["suggestedPrompts"])} prompts')

print('\n=== All Agents ===')
for agent in data['agents']:
    print(f'  ✓ {agent["name"]}')
