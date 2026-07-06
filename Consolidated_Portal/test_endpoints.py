import urllib.request, urllib.parse, json

# Test legacy endpoint
data = urllib.parse.urlencode({'prompt': 'hello world function'}).encode()
try:
    r = urllib.request.urlopen('http://localhost:8080/api/generate_code', data, timeout=5)
    print('generate_code: HTTP 200 OK')
except urllib.error.HTTPError as e:
    print(f'generate_code: HTTP {e.code} - {e.read().decode()[:200]}')
except Exception as e:
    print(f'generate_code error: {e}')

# Test summarize endpoint
data2 = urllib.parse.urlencode({'text': 'This is a long document to summarize.'}).encode()
try:
    r2 = urllib.request.urlopen('http://localhost:8080/api/summarize', data2, timeout=5)
    print('summarize: HTTP 200 OK')
except urllib.error.HTTPError as e:
    print(f'summarize: HTTP {e.code} - {e.read().decode()[:200]}')
except Exception as e:
    print(f'summarize error: {e}')
