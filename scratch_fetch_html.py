import urllib.request

url = 'http://127.0.0.1:8000/'
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
    with open('d:/knowledgebase/static/test_exact_original.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Successfully saved {len(html)} bytes to d:/knowledgebase/static/test_exact_original.html")
except Exception as e:
    print(f"Error fetching URL: {e}")
