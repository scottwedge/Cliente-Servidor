import zmq
import argparse
import hashlib
import os

def getReadSize():
    READ_SIZE = 1024 #Cuantos bits va a leer por parte, en este caso 1KB
    return READ_SIZE


def extraerHash_data(data):
    key = hashlib.sha1(data)
    return key.hexdigest()

def extraerHash_nameFile(nameFile):
    key =  hashlib.sha1()
    file_size = os.stat(nameFile).st_size
    READ_SIZE = getReadSize()
    with open(nameFile, 'rb') as f:
        part = 0
        while READ_SIZE * part < file_size:
            #La funcion f.seek mueve el puntero a los bits que nosotros le damos, 
            #Como el segundo argumento es cero, indica que mueve el puntero con 
            #relacion al inicio del archivo
            f.seek(READ_SIZE*part, 0)
            #Actualizamos el hash en cada parte que leemos
            key.update(f.read(READ_SIZE))
            part += 1
    return key.hexdigest()


def downloadFile(nameFile, socket):
    socket.send_multipart([b"download", nameFile.encode("utf-8")])
    msg = socket.recv_multipart()

    if msg[0].decode("utf-8") == "No existe":
        print("No se encontro el archivo especificado")
        return 

    while msg[0].decode("utf-8") == "sending":
        with open("archivosDescargados/" + nameFile, "ab") as f:
            
            
                f.write(msg[1])
                socket.send_string("ok")
                msg = socket.recv_multipart()
    
    print("La operacion de descarga ha finalizado")

def uploadFile(nameFile, socket):
    #Calculando el tamanio para saber cuantas partes leer
    file_size = os.stat(nameFile).st_size
    big_hash = extraerHash_nameFile(nameFile) #Sacamos el hash de todo el archivo
    print("Enviando archivo con hash", big_hash)
    READ_SIZE = getReadSize()
    #Como el nombre del archivo tiene aparte la carpeta 
    #'archivos/', le quitamos esta parte con un split
    nameFile_withoutPath = nameFile.split("/")[-1]

    with open(nameFile, 'rb') as f:
        part = 0
        
        duplicatedFile = False
        while READ_SIZE * part < file_size and not duplicatedFile:
            #La funcion f.seek mueve el puntero a los bits que nosotros le damos, 
            #Como el segundo argumento es cero, indica que mueve el puntero con 
            #relacion al inicio del archivo
            f.seek(READ_SIZE*part, 0)
            data = f.read(READ_SIZE) #Extraemos los bits de la parte
            hash_part = extraerHash_data(data).encode("utf-8") #Le sacamos el hash a la parte
            if part == 0:
                firstPart = b"True"
            else:
                firstPart = b"False"
            #Enviamos todo en un multipart
            socket.send_multipart([b"upload", nameFile_withoutPath.encode("utf-8"), 
                                    big_hash.encode("utf-8"), 
                                    hash_part, 
                                    data, firstPart])

            server_response = socket.recv_string()
            print("Respuesta del servidor: ", server_response)

            duplicatedFile = server_response == "Archivo duplicado" #Instruccion break disimulada
            part += 1

def crateParserConsole():
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

if __name__ == "__main__":
    args = crateParserConsole()
    action = args.action

    context = zmq.Context()
    
    #  Socket to talk to server
    print("Conectando")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    if action == "upload":
        uploadFile("archivos/" + args.file, socket)

    elif action == "download":
        downloadFile(args.file, socket)  
    else:
        socket.send_multipart([action.encode("utf-8")])
        print(socket.recv_string())



    



