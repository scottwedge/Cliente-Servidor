import argparse
import zmq
import netifaces
from string import ascii_letters
import random
import hashlib
from os import listdir, remove
from os.path import isfile, join
from abstractServer import Server
"""
Servidor que sera parte del anillo, entrando por un servidor ya perteneciente 
a este.
EL servidor generara la llave con su MAC y una cadena aleatoria de 40 caracteres,
luego le preguntara a cada servidor del anillo 
si esa llave esta en el rango que el maneja, si si esta en el rango, 
el servidor miembro del anillo cambiara su sucesor por el servidor nuevo, y 
le cedera los archivos que esten entre la llave del nuevo servidor y el tope 
del rango que tenia anteriormente, tambien cambiara su rango entre el rango 
minimo que tenia anteriormente y la llave dada por el nuevo servidor. Por su
parte, el servidor nuevo creara el sucesor, que sera el sucesor del servidor
viejo, y creara su rango de llaves, que ira desde la llave generada por este
y el rango maximo del anterior servidor
"""
class NormalServer(Server):

    def __init__(self, ip, port, folder_name, default_server):
        super().__init__(ip, port, folder_name)
        self.default_server = default_server
        self.connectToRing()

    def findResponsabilitie(self):
        #AL entrar al anillo debe buscar cual es su lugar, por lo que 
        #va servidor a servidor hasta que alguno le dice donde va
        socket_req = self.context.socket(zmq.REQ)
        sock_addr = "tcp://" + self.default_server
        socket_req.connect(sock_addr)
        data = {
            "action" : "new_server",
            "key" : self.max_key,     
        }
        socket_req.send_json(data)
        response = socket_req.recv_json()
        sock_predecessor = response["predecessor"]
        while not response["responsabilitie"]:
            socket_req.disconnect(sock_addr)
            sock_addr = "tcp://" + response["sucessor"]
            socket_req.connect(sock_addr)
            socket_req.send_json(data)
            response = socket_req.recv_json()
            sock_predecessor = response["predecessor"]
        
        return (socket_req, response,  sock_predecessor)


    #Al iniciar un servidor, se conecta al anillo, yendo servidor a 
    #servidor buscando el sitio que le corresponde 
    def connectToRing(self):
        socket_req, response, sock_predecessor = self.findResponsabilitie()
        self.predecessor = sock_predecessor
        print("Predecessor", sock_predecessor)
        #Encontro su lugar
        self.sucessor = response["sucessor"]
        self.socket_sucessor = socket_req
        self.sucessor_connected = True
        self.min_key = int(response["min_key"])
        self.socket_sucessor.send_json({"ip":self.ip, "port":self.port})
        
        self.receiveFiles(socket_req, "sucessor")
        
        #Este era el socket que conectaba con el sucesor, pero como ya 
        #tenemos un atributo para eso, lo usamos para contactarnos con el 
        #predecesor
        sock_predecessor = self.context.socket(zmq.REQ)
        #Ahora, el servidor nuevo debe enviar al predecesor la notificacion
        #para que cambie de sucesor, y debe pedirle la max_key para ponerla 
        #como min_key aqui.
        sock_predecessor.connect("tcp://" + self.predecessor)
        sock_predecessor.send_json({"action":"change_sucessor", 
                              "sucessor" : self.ip + ":" + self.port})
        response = sock_predecessor.recv()

        print("Succefully connected to ring")
        print("Sucessor: ", self.sucessor)
        print("Min key:", str(self.min_key)[:4], len(str(self.min_key)))
        print("Max key:", str(self.max_key)[:4], len(str(self.max_key)))


def crateParserConsole():
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", type=str)
    parser.add_argument("port", type=str)
    parser.add_argument("folder", type=str)
    parser.add_argument("serverInTheRing", type=str)
    return parser.parse_args()


if __name__ == "__main__":
    args = crateParserConsole()
    server = NormalServer(args.ip, args.port, args.folder, args.serverInTheRing)
    server.listen()
