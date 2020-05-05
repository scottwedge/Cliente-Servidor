import zmq
import netifaces
from string import ascii_letters
import random
import hashlib
from os import listdir, remove
from os.path import isfile, join
from abc import ABC

class Server(ABC):

    #Verifica si la llave que le llega como parametro esta en el rango 
    def keyInRange(self, key):
        return ((self.min_key < self.max_key and  #Rango unico [x, y]
                 key > self.min_key and key <= self.max_key) 
                 or
                (self.min_key >= self.max_key and #Rango partido [x, y] U [z, w]
                 (key <= self.max_key or key > self.min_key)))


    #Se crea el socket con el que atendera a los clientes y a otro servidor
    #cuando desea unirse al anillo
    def createSocket(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://" + self.ip + ":" + self.port)

        self.sucessor = ""
        self.socket_sucessor = self.context.socket(zmq.REQ)
        self.sucessor_connected = False

    #Guarda un archivo
    def saveFile(self, data, hashName):
        with open("archivos/" + self.folder_name + "/" + hashName, "wb") as f:
            f.write(data)

    #Envia los datos de un archivo guardado
    def downloadFile(self):
        hash = self.message["hash"] 
        key = int(hash, 16)
        if self.keyInRange(key):
            print("Downloading file")  
            with open("archivos/" + self.folder_name + "/" + hash, "rb") as f:
                data = f.read()
            self.socket.send_multipart([b"True", data])
        else:
            self.socket.send_multipart([b"False", self.sucessor.encode("utf-8")])

    #Verifica si el json ya existe, si no, recibe los datos y los
    # envia a la funcion saveFile  
    def saveData(self, key, isJson):
        hash = self.message["hash"]
        #Si es el archivo de metadata debe verificar que no exista
        if isJson:
            path = join('archivos', self.folder_name)
            files = [f for f in listdir(path) if isfile(join(path, f))]
            if hash in files:
                print("Se intento subir un json que ya existe")
                self.socket.send_string("Ya existe")
                return 
        
        print(f"Uploading file {str(key)[:4]} {len(str(key))}")  
        self.socket.send_string("send_data")
        data = self.socket.recv()  
        self.saveFile(data, hash)
        self.socket.send_string("Saved")


    #Llama a 'save file' con los datos y el nombre, luego notifica
    #que el archivo fue guardado
    def uploadFile(self, isJson = False):
        key = int(self.message["hash"], 16)
        if self.keyInRange(key):
            #Si esta en el rango de llaves que le corresponden a este servidor
            self.saveData(key, isJson)
        else:
            self.socket.send_string(self.sucessor)
    
    def changeSucessor(self):
        #Cambia de sucesor cuando un nuevo nodo entra al anillo
        if self.sucessor_connected:
            self.socket_sucessor.disconnect(f"tcp://{self.sucessor}")
        else:
            self.sucessor_connected = True
            
        self.sucessor = self.message["sucessor"]
        self.socket_sucessor.connect(f"tcp://{self.sucessor}")
        print("New sucessor", self.sucessor)
        self.socket.send(b" ")

    def send_files_old_server(self):
        #Cuando el servidor se desconecta, una de las operaciones que 
        #debe hacer antes de morir es enviarle todos los archivos que
        #tenia a su sucesor
        path = join("archivos", self.folder_name)
        for f in listdir(path):
            if isfile(join(path, f)):
                with open(join(path, f), 'rb') as g:
                    data = g.read()
                remove(join(path, f))
                print("Sending", f[:4], len(f))
                self.socket_sucessor.send_json({
                                        "action" : "file", 
                                        "hash" : f, 
                                        })
                self.socket_sucessor.recv()
                self.socket_sucessor.send(data)
                self.socket_sucessor.recv()
        self.socket_sucessor.send_json({'action' : "end"})
        self.socket_sucessor.recv()
    
    def disconnectFromRing(self, keyInterrupt = False):
        #Si se desconecta del anillo se debe:
        #-Avisar al sucesor que se esta desconectando para que 
        #reciba los archivos, cambie el predecesor y cambie su min key
        #-Avisar al predecesor que se esta desconectando y que cambie su 
        #sucesor
        #-Enviar los archivos al sucesor
        print("Sending disconnect to sucessor", self.sucessor)
        self.socket_sucessor.send_json({
            "action" : "disconnect_predecessor",
            "min_key" : self.min_key, #Le envia la nueva min_key al sucesor
            "predecessor" : self.predecessor
        })

        
        self.socket_sucessor.recv()
        print("Sending all files")
        #Envio de todos los archivos
        self.send_files_old_server()

        sock_pred = self.context.socket(zmq.REQ)
        sock_pred.connect("tcp://" + self.predecessor)
        sock_pred.send_json({
            "action" : "change_sucessor",
            "sucessor" : self.sucessor
        })
        if not keyInterrupt:
            #Si se salio por ctrl+c, no habra sido el cliente el que mando
            #la solicitud, por lo que no tiene que enviar respuesta a nadie
            self.socket.send_string("Server disconnected :(")
        print("Disconnected")
        
    def receiveFiles(self, socket, from_server):
        #Recibe los archivos que le corresponden, puede ser porque
        #acaba de conectarse (recibe archivos del sucesor) o 
        #porque el predecesor se va a desconectar
        msg = socket.recv_json()
        while msg["action"] == "file":
            hash = msg["hash"]
            socket.send(b" ")
            data = socket.recv()
            with open(join("archivos", self.folder_name, hash), 'wb') as f:
                f.write(data)
            print("Received file from server", hash[:8], len(hash))
            socket.send(b" ")
            msg = socket.recv_json()
        if from_server == "predecessor":
            #Si esta recibiendo archivos del predecesor, quiere decir que 
            #el socket es de tipo REPLY (el socket del servidor normal), 
            # por lo que finaliza la funcion
            #enviando algo (Cuando se desconecta un server)
            socket.send(b" ")

    def predecessorDisconneccted(self):
        #Cambiando el predecesor y min key, luego recibiendo archivos
        self.min_key = self.message["min_key"]
        self.predecessor = self.message["predecessor"]
        print("New predecessor", self.predecessor)
        self.socket.send(b" ")
        self.receiveFiles(self.socket, "predecessor")

    #Menu de entrada para todas las acciones que le lleguen al servidor
    def listen(self):
        
        while True:
            # print("Listening")
            #  Wait for next request from client
            try:
                self.message = self.socket.recv_json()
            except KeyboardInterrupt:
                self.disconnectFromRing(keyInterrupt = True)
                break
            else:
                action = self.message["action"]
            # print("Action: ", action)
            if action == "upload":
                self.uploadFile()

            elif action == "download":
                self.downloadFile()
            
            elif action == "new_server":
                self.newServer()
            
            elif action == "change_sucessor":
                self.changeSucessor()
            
            elif action == "disconnect":
                self.disconnectFromRing()
                break
            elif action == "disconnect_predecessor":
                self.predecessorDisconneccted()

            elif action == "upload_json":
                self.uploadFile(isJson = True)
                

    #Con la direccion mac y una cadena aleatoria de 40 caracteres, al 
    #hacerle sha1 a esto, el resultado sera el rango minimo de llaves
    #que el servidor alojara
    def createKey(self):
        inter = netifaces.interfaces()[1]
        my_mac = netifaces.ifaddresses(inter)[netifaces.AF_LINK][0]['addr']
        for i in range(40):
            my_mac += random.choice(ascii_letters)
        my_mac = my_mac.encode("utf-8")
        m = hashlib.sha1()
        m.update(my_mac)
        
        self.max_key = int(m.hexdigest(), 16)
        self.min_key = ""
        print("Id:", str(self.max_key)[:4], len(str(self.max_key)))

    #Cuando un servidor nuevo llega, y la llave enviada esta en el rango del
    #servidor actual, este le envia todos los archivos entre la llave dada y 
    #el rango maximo, adicionalmente, los borra de este servidor
    def send_files_new_server(self):
        path = "archivos/" + self.folder_name
        for f in listdir(path):
            if isfile(join(path, f)):
                min_key = int(self.min_key)
                max_key = int(self.max_key)
                key = int(f, 16)
                if ((min_key < max_key and (key <= min_key or key > max_key)) or 
                    (min_key >= max_key and key <= min_key and key > max_key)):

                    print(f"Sending files to new server: {str(key)[:4]} {len(str(key))}")
                    with open(join(path, f), 'rb') as g:
                        data = g.read()
                    remove(join(path, f))
                    self.socket.send_json({"action" : "file", 
                                            "hash" : f, 
                                            })
                    self.socket.recv()
                    self.socket.send(data)
                    self.socket.recv()
        self.socket.send_json({'action' : "end"})

    #Puerta de entrada de cada servidor cuando quieren entrar al anillo, 
    #aqui se valida que la llave este en el rango del servidor actual 
    def newServer(self):
        key = self.message["key"]

        #Cuando el servidor es el sucesor del nuevo
        if self.keyInRange(key):
            self.socket.send_json({'responsabilitie' : True, 
                                'sucessor' : self.ip + ":" + self.port, 
                                'predecessor' : self.predecessor, 
                                'min_key' : self.min_key})
            
            response = self.socket.recv_json()
            self.predecessor = response["ip"] + ":" + response["port"]
            print("New predecessor", self.predecessor)
            self.min_key = key
            print("Min key changed", str(self.min_key)[:4], 
                                    len(str(self.min_key)))

            self.send_files_new_server()
        else: #El servidor no es el sucesor del nuevo nodo
            self.socket.send_json({'responsabilitie' : False, 
                                    'sucessor' : self.sucessor, 
                                    'predecessor' : self.predecessor
                                    })
    
    def __init__(self, ip, port, folder_name):
        self.ip = ip
        self.port = port
        self.folder_name = folder_name
        self.createKey()
        self.createSocket()
