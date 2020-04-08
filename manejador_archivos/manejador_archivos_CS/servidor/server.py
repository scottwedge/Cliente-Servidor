import time
import zmq
import hashlib
import os
import json 

NAME_DATAFILE = "dataFiles.json" #Json que mapea hash global con lista de hashes
information_dict = {}


NAME_NAMEFILES = "nameFiles.json" #Json que mapea nombre con hash global
names_dict = {}

with open(NAME_DATAFILE, "r") as dataFiles:
    information_dict = json.load(dataFiles)
with open(NAME_NAMEFILES, "r") as dataFiles:
    names_dict = json.load(dataFiles)




def extraerHash(data):
    result = hashlib.sha1(data)
    return result.hexdigest()

def saveFile(data, hashName):
    with open("archivos/" + hashName, "wb") as f:
        f.write(data)

def updateJson(nameFile, jsonObj):
    with open(nameFile, "w") as f:
        f.write(json.dumps(jsonObj))

def downloadFile(message, socket):
    nameFile = message[1].decode("utf-8")
    if nameFile not in names_dict:
        socket.send_multipart([b"No existe", b"i"])
    else:
        
        hash_global = names_dict[nameFile]
        hashes_part = information_dict[hash_global]
        for hash in hashes_part:
            with open("archivos/" + hash, "rb") as f:
                data = f.read()
            socket.send_multipart([b"sending", data])
            socket.recv_string()
        socket.send_multipart([b"end", b"i"])

def uploadFile(message, socket):
    nameFile = message[1].decode("utf-8")
    bigHash = message[2].decode("utf-8")
    hashFile = message[3].decode("utf-8")
    data = message[4]
    firstPart = message[5].decode("utf-8")
    if firstPart == "True":
        if bigHash in information_dict:
            socket.send_string("Archivo duplicado")
        else:
            if nameFile in names_dict:
                socket.send_string("Ya existe un archivo con este nombre")
            else:
                names_dict[nameFile] = bigHash
                information_dict[bigHash] = [hashFile]
                updateJson(NAME_NAMEFILES, names_dict)
                updateJson(NAME_DATAFILE, information_dict)
                
                saveFile(data, hashFile)
                socket.send_string("Saved")
    else:
        information_dict[bigHash].append(hashFile)
        updateJson(NAME_DATAFILE, information_dict)
        saveFile(data, hashFile)
        socket.send_string("Saved")


if __name__ == "__main__":
    
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")


    accion = ""
    nombreArchivo = ""
    while True:
        #  Wait for next request from client
        message = socket.recv_multipart()
        action = message[0].decode("utf-8")
        #print("Action: ", action)


        if action == "upload":
            uploadFile(message, socket)


        elif action == "download":
            downloadFile(message, socket)

        else:
            list_names = ""
            for name in names_dict:
                list_names += name + "\n"
            socket.send_string(list_names[:-1])
        
        