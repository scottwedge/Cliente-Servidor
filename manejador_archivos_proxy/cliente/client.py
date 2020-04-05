import zmq
import argparse
import hashlib
import os
import json


def createParserConsole():
        parser = argparse.ArgumentParser()

        parser.add_argument("action", type=str)
        parser.add_argument("--file", "-f",  type = str, default= "")

        args = parser.parse_args()
        action = args.action

        if action not in ["upload", "download", "list"]:
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
    read_size = 1024 * 512 #Tamanio de lectura, 512KB

    def downloadFile(self):

        self.socket_proxy.send_multipart([b"download", self.args.file.encode("utf-8")])
        msg = self.socket_proxy.recv_json()

        #Depuracion previa al metodo
        if msg["hashes"] == "Error":
            print("No se encontro el archivo especificado")
            return 


        #Recibe la lista de hashes con su respectivo servidor, 
        # el cliente tiene un diccionario de tipo dir_server -->socket, 
        #si no tiene el servidor en este dict, lo agrega y luego le envia la 
        #informacion
        hashes = msg['hashes']
        servers = msg['servers']
        with open("archivosDescargados/" + self.args.file, 'ab') as f:
            for (hash, server) in zip(hashes, servers):
                if server not in self.sockets_servers:
                    ip, port = server.split(":")
                    self.createSocket(ip, port)

                sock_server = self.sockets_servers[server]
                sock_server.send_multipart([b"download", hash.encode("utf-8")])
                data = sock_server.recv()
                f.write(data)
        print("La operacion de descarga ha finalizado")


    def obtain_servers(self):
        #Obtiene la lista de servidores a los que les debe enviar el 
        #archivo (las partes del archivo)
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
        self.socket_proxy.send_multipart([b"upload", metadata])

        servers = self.socket_proxy.recv_multipart()
        if servers[0].decode("utf-8") == "Error":
            print("Un error ha ocurrido: ", servers[1].decode("utf-8"))
            return [[], []]
        
        return (servers, hashes)

    def uploadFile(self):
        servers, hashes = self.obtain_servers()
        if servers == []:
            return 0
        #Luego de que el proxy le mande la lista de servidores, 
        #el cliente va servidor a servidor subiendo la parte
        with open("archivos/" + self.args.file, 'rb') as f:
            i = 0
            for (hash, server) in zip(hashes, servers):
                server = server.decode("utf-8")
                if server not in self.sockets_servers:
                    ip, port = server.split(":")
                    self.createSocket(ip, port)

                
                f.seek(self.read_size*i, 0)
                data = f.read(self.read_size)
                socket_server = self.sockets_servers[server]
                print("Sending to", server)
                socket_server.send_multipart([b"upload", hash.encode("utf-8"), 
                                              data])
                print("Message from server: ", socket_server.recv_string())
                i += 1

        print("The upload ended")

    def createSocket(self, ip = None, port = None):
        if ip == None:
            #  Para el proxy
            self.socket_proxy = self.context.socket(zmq.REQ)
            self.socket_proxy.connect("tcp://localhost:5555")
        else:
            #Nuevo servidor descubierto
            temp_socket = self.context.socket(zmq.REQ)
            temp_socket.connect("tcp://" + ip + ":" + port)
            self.sockets_servers[ip+":"+port] = temp_socket

    def chooseOption(self):
        action = self.args.action
        if action == "upload":
            self.uploadFile()

        elif action == "download":
            self.downloadFile()  
        else: #List
            self.socket_proxy.send_multipart([action.encode("utf-8")])
            print(self.socket_proxy.recv_string())

    def __init__(self, args):
        self.args = args
        self.context = zmq.Context()
        self.sockets_servers = {}
        self.createSocket()
        

if __name__ == "__main__":
    client = Client(createParserConsole())
    client.chooseOption()