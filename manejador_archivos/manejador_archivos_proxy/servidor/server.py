import argparse
import zmq

class Server:
    def createSocket(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://" + self.ip + ":" + self.port)

        

    def notifyProxy(self):
        #Debemos hacer que por un momento este servidor actue como cliente 
        #para avisarle al proxy que se creo uno nuevo, luego de esto 
        #cerramos el socket porque nunca mas lo necesitaremos
        socket_to_proxy = self.context.socket(zmq.REQ)
        socket_to_proxy.connect("tcp://localhost:5555")
        socket_to_proxy.send_multipart([b"new_server", 
                                        self.ip.encode("utf-8"), 
                                        self.port.encode("utf-8")])
        msg = socket_to_proxy.recv_string()
        print("Message from proxy:", msg)
        socket_to_proxy.close()

    def saveFile(self, data, hashName):
        with open("archivos/" + self.folder_name + "/" + hashName, "wb") as f:
            f.write(data)


    def downloadFile(self): 
        hash = self.message[1].decode("utf-8")
        with open("archivos/" + self.folder_name + "/" + hash, "rb") as f:
            data = f.read()
            self.socket.send(data)

    def uploadFile(self):
        hashFile = self.message[1].decode("utf-8")
        data = self.message[2]    
        self.saveFile(data, hashFile)
        self.socket.send_string("Saved")


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

    def __init__(self, ip, port, folder_name):
        
        self.ip = ip
        self.port = port
        self.folder_name = folder_name
        self.createSocket()
        self.notifyProxy()


def crateParserConsole():
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", type=str)
    parser.add_argument("port", type=str)
    parser.add_argument("folder", type=str)
    return parser.parse_args()


if __name__ == "__main__":
    args = crateParserConsole()
    server = Server(args.ip, args.port, args.folder)
    server.listen()
