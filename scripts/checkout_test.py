import json
import urllib.request
import urllib.error

url = 'http://127.0.0.1:8000/checkout/'
data = json.dumps([{'id': 1, 'name': 'Jean', 'price': 50, 'qty': 2}]).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')

try:
    resp = urllib.request.urlopen(req)
    print('STATUS', resp.status)
    print(resp.read().decode())
except urllib.error.HTTPError as e:
    print('STATUS', e.code)
    print(e.read().decode())
except Exception as e:
    print('ERR', e)
