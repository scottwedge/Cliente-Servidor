import json
import hashlib
with open("dataFiles.json", "r") as f:
    data_json = json.load(f)
with open("nameFiles.json", "r") as f:
    names_json = json.load(f)

nameFile = "archivo0"

global_hash = names_json[nameFile]

list_hashes = data_json[global_hash]

key = hashlib.md5()
for hash in list_hashes:
    with open("archivos/" + hash, "rb") as f:
        key.update(f.read())

print("Initial key", global_hash)
print("Obtained key", key.hexdigest())