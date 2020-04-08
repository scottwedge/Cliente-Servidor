import zmq
import argparse
import hashlib
import os
from os.path import join
import json



def createParserConsole():
        parser = argparse.ArgumentParser()
        parser.add_argument("initialServer", type = str)
        parser.add_argument("action", type=str)
        parser.add_argument("--file", "-f",  type = str, default= "")
        args = parser.parse_args()
        action = args.action

        if action not in ["upload", "download", "list", "disconnect"]:
            raise Exception("Comando no valido")

        if action in ["upload", "download"] and not args.file:
            raise Exception("Se debe escribir el archivo")

        if action == "list" and args.file:
            raise Exception("Al listar no se necesita un archivo")

        return args


def extraerHash_data(data):
    key = hashlib.sha1(data)
    return key.hexdigest()

def extraerHash_nameFile(nameFile, read_size):
    key =  hashlib.sha1()
    hashes = []
    file_size = os.stat(nameFile).st_size
    
    with open(nameFile, 'rb') as f:
        part = 0
        while read_size * part < file_size:
            #La funcion f.seek mueve el puntero a los bits que nosotros le damos, 
            #Como el segundo argumento es cero, indica que mueve el puntero con 
            #relacion al inicio del archivo
            f.seek(read_size*part, 0)
            #Actualizamos el hash en cada parte que leemos
            data = f.read(read_size)
            key.update(data)
            hashes.append(extraerHash_data(data))
            part += 1
    return (key.hexdigest(), hashes)

class Client:
    
    read_size = 1024 * 512 #Tamanio de lectura, en este caso 512KB


    def disconnectServer(self):
        #Decirle a un servidor que se desconecte del anillo
        temp_socket = self.context.socket(zmq.REQ)
        temp_socket.connect("tcp://" + self.default_server)
        temp_socket.send_json({
            "action" : "disconnect"
        })
        print("Msg from server:", temp_socket.recv_string())


    #Manda una solicitud al anillo de obtener los datos de un archivo con hash
    def obtainData(self, hash):
        data_to_send = {
            "action" : "download",
            "hash" : hash
        }
        self.initial_socket.send_json(data_to_send)
        resp = self.initial_socket.recv_multipart()
        
        #Mientras que no sea un archivo va ir buscando servidor a servidor
        while resp[0].decode("utf-8") != "True": 
            temp_socket = self.context.socket(zmq.REQ)
            temp_socket.connect("tcp://" + resp[1].decode("utf-8"))

            temp_socket.send_json(data_to_send)
            resp = temp_socket.recv_multipart()
        data = resp[1]
        return data 

    def downloadFile(self):
        torrent = self.args.file
        metadata = json.loads(self.obtainData(torrent).decode("utf-8"))

        print("Downloading file with big hash", metadata["global_hash"])
        hashes = metadata["list_hashes"]
        with open(join("archivosDescargados", metadata["name"]), "ab") as f:
            for part, hash in enumerate(hashes):
                data = self.obtainData(hash)
                f.write(data)
                print(f"Part {part} recived")
        print("La descarga ha finalizado")
    


    #Busca de servidor en servidor quien es el responsable de guardar un
    #archivo, si el archivo a subir es el de metadata, el servidor verificará 
    #si ya lo tiene, para así no subir todo el archivo
    def send_data(self, data, hash, isJson = False):
        if isJson:
            action = "upload_json"
        else:
            action = "upload"
        json_data = {
            "action" : action,
            "hash" : hash
        }
        self.initial_socket.send_json(json_data)
        response = self.initial_socket.recv_string()
        temp_socket = self.initial_socket
        #Mientras no encuentre al servidor responsable, ir de serv
        #en serv
        while response != "send_data" and response != "Ya existe":
            temp_socket = self.context.socket(zmq.REQ)
            temp_socket.connect("tcp://" + response)
            temp_socket.send_json(json_data)
            response = temp_socket.recv_string()

        if isJson and response == "Ya existe":
            print("El archivo que esta intentando subir ya existe")
            return False
        else:
            temp_socket.send(data)
            temp_socket.recv_string()
            return True


    #Funcion que saca el global hash y la lista de hashes para crear el archivo
    #de metadata que tambien ingresara al anillo.
    def save_metadata(self):
        nameFile = "archivos/" + self.args.file
        #Calculando el tamanio para saber cuantas partes leer
        big_hash, hashes = extraerHash_nameFile(nameFile, self.read_size) 
        print("Enviando archivo con hash", big_hash)
        metadata = {
            "name" : self.args.file, 
            "global_hash" : big_hash, 
            "list_hashes" : hashes
        }
        metadata = json.dumps(metadata).encode("utf-8")
        hash_metadata = extraerHash_data(metadata)
        if self.send_data(metadata, hash_metadata, isJson=True):
            print("Saved metadata")
            return hashes, hash_metadata
        else: 
            return ([], None)

    #Luego de guardar la metadata, esta funcion manda a guardar todas las partes
    #del archivo
    def uploadFile(self):
        hashes, torrent = self.save_metadata()
        if hashes == []:
            return 


        with open("archivos/" + self.args.file, 'rb') as f:
            
            for part, hash in enumerate(hashes):
                f.seek(self.read_size*part, 0)
                data = f.read(self.read_size)
                self.send_data(data, hash)
                print("Saved part", part)

        print("The upload has ended")
        print("Torrent: ", torrent)

    def createSocket(self):
        self.context = zmq.Context()

        self.initial_socket = self.context.socket(zmq.REQ)
        self.initial_socket.connect("tcp://" + self.default_server)

    def chooseOption(self):
        action = self.args.action
        if action == "upload":
            self.uploadFile()

        elif action == "download":
            self.downloadFile() 
        elif action == "disconnect":
            self.disconnectServer() 
      


    def __init__(self, args):
        self.args = args
        self.default_server = args.initialServer
        self.createSocket()
        
        
if __name__ == "__main__":
    client = Client(createParserConsole())
    client.chooseOption()



