# fetch reviews and store as json

import json
import urllib.request

API_EP = "https://komura-api.vercel.app/api/danish"

with urllib.request.urlopen(API_EP) as url:
    data = json.loads(url.read().decode())

with open('_data/old_reviews.json') as f:
    old_data = json.loads(f.read())

new_data = {"data": []}
for i, book in enumerate(data["data"]):
    if len(book['review']['body'].strip()) == 0:
        for j, old_book in enumerate(old_data["data"]):
            if book['book']['title'].lower() in old_book['book']['title'].lower() \
                or old_book['book']['title'].lower() in book['book']['title'].lower():
                new_data["data"].append(old_book)
                break
    else:
        new_data["data"].append(book)

with open('_data/reviews.json', 'w+') as f:
    json.dump(new_data, f)
