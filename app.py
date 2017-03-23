import requests

url = 'http://localhost:8080/post'
files = [
    ('a', ('test-a.jpg',open('test-a.jpg', 'rb'), 'image/jpg')),
    ('b', ('test-b.jpg',open('test-b.jpg', 'rb'), 'image/jpg'))
    ]
headers = {'x-mod-id': '2'}

r = requests.post(url, files=files, headers=headers)
print(r.text)