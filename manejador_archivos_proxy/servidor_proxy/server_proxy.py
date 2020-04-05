import zmq
import json

class ProxyServer():

    def createSocket(self):
        #Se crea el socket del proxy
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")

    def uploadFile(self):
        json_file = self.message[1].decode("utf-8")
        metadata = json.loads(json_file)

        #Depuracion antes del metodo
        if  metadata["name"] in self.name_files:
            self.socket.send_multipart([b"Error", b"Ya existe el nombre"])
            return 

        if metadata["global_hash"] in self.data_files:
            self.socket.send_multipart([b"Error", 
                                        b"Ya existe este archivo con otro nombre"])
            return 

        #Se agrega nombre ->hash global al diccionario de nombres
        self.name_files[metadata["name"]] = metadata["global_hash"]


        #Se crea la lista de servidores que se le entregara al cliente, 
        #con la variable pos_pinter_server podemos garantizar un 
        #balanceo de carga
        list_servers = []
        n_servers = len(self.servers)
        for i in range(len(metadata["list_hashes"])):
        
            self.pos_pointer_server = self.pos_pointer_server % n_servers

            #Obtenemos el servidor que sera responsable de esa parte
            ip, port, files = self.servers[self.pos_pointer_server]
            self.servers[self.pos_pointer_server][2] = files+1
            sock_server = ip + ":" + port
            #Lo agregamos a la lista de servidores
            list_servers.append(sock_server)
            self.pos_pointer_server += 1
        
        #Agregamos al diccionario 'data_files' la lista de hashes para 
        # un hash global y la lista de servidores que contienen cada hash
        self.data_files[metadata["global_hash"]] = [metadata["list_hashes"], 
                                                    list_servers]
        self.socket.send_multipart([l.encode("utf-8") for l in list_servers])

    def downloadFile(self):
        name = self.message[1].decode("utf-8")
        #Depuracion previa al metodo
        if name not in self.name_files:
            self.socket.send_json({'hashes' : 'Error'})
            return 
        

        #Le enviamos la lista de servidores y los hashes de las partes 
        #que componen el archivo al cliente
        global_hash = self.name_files[name]
        hashes_and_servers = self.data_files[global_hash]
        metadata = {
            'hashes' : hashes_and_servers[0],
            'servers' : hashes_and_servers[1]
        }

        print("Sending file with global hash", global_hash)
        self.socket.send_json(metadata)
        


    def newServer(self):
        ip_server = self.message[1].decode("utf-8")
        port_server = self.message[2].decode("utf-8")
        #Agregamos en una lista al servidor, de la forma
        #(IP, puerto, archivos_almacenados)
        self.servers.append([ip_server, port_server, 0])
        print(f"Totally, I have {len(self.servers)} servers")
        self.socket.send_string("New server added")


    def listen(self):
        while True:
            #  Wait for next request from client
            self.message = self.socket.recv_multipart()
            action = self.message[0].decode("utf-8")
            print("Action: ", action)


            if action == "upload":
                self.uploadFile()


            elif action == "download":
                self.downloadFile()

            elif action == "list":
                list_names = ""
                for name in self.name_files:
                    list_names += name + "\n"
                self.socket.send_string(list_names[:-1])
            elif action == "new_server":
                self.newServer()


    def __init__(self):
        self.createSocket()
        self.servers = []
        self.name_files = {}
        self.data_files = {}

        #Con 'pos_pointer_server' se le entrega un archivo al servidor
        #con el indice que coincida con esta variable
        self.pos_pointer_server = 0 

if __name__ == "__main__":
    proxy_server = ProxyServer()
    proxy_server.listen()
 