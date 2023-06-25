import json

with open('./keys.json') as filess:
    data = json.load(filess)
    print(data)