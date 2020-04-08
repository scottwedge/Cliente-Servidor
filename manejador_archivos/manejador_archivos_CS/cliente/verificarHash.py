import os
import hashlib
import argparse

def extraerHash_nameFile(nameFile):
    key =  hashlib.sha1()
    file_size = os.stat(nameFile).st_size
    read_size = 1024 #Cuantos bits va a leer por parte, en este caso 1KB
    with open(nameFile, 'rb') as f:
        part = 0
        while read_size * part < file_size:
            #La funcion f.seek mueve el puntero a los bits que nosotros le damos, 
            #Como el segundo argumento es cero, indica que mueve el puntero con 
            #relacion al inicio del archivo
            f.seek(read_size*part, 0)
            #Actualizamos el hash en cada parte que leemos
            key.update(f.read(read_size))
            part += 1
    return key.hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument("nameFile", type=str)
args = parser.parse_args()
nameFile = "archivosDescargados/" + args.nameFile
print(extraerHash_nameFile(nameFile))