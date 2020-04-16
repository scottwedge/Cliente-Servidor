"""
    1.Recoge los clusters, los tags y la suma
     para cada centroide de los workers
        a. Pega los clusters parciales
        b. Promedia la suma de los puntos para cada centroide

"""

import zmq 
import numpy as np
import argparse
import time
from sklearn.datasets import make_blobs
from os.path import join 
import pandas as pd 
class Sink:

    #Crea el socket donde le llega la informacion del 
    #ventilator, que son el numero de clusters
    def createSockets(self):
        self.context = zmq.Context()

        self.from_ventilator = self.context.socket(zmq.PULL)
        self.from_ventilator.bind(f"tcp://{self.dir_sink}")

        self.to_ventilator = self.context.socket(zmq.REQ)
        self.to_ventilator.connect(f"tcp://{self.dir_ventilator}")


    def recieveFirstMessage(self):
        msg = self.from_ventilator.recv_json()
        self.iters = msg["iters"] #Numero de veces que se corre el kmeans
        self.opers = msg["opers"] #Numero de tareas paralelizadas para calcular 
                                  #la distorsion en cada momento que se corre kmeans
        print("Recieve first message")

    #Funcion donde le llegara el mensaje del ventilator
    def listen(self):
        print("Ready")
        self.recieveFirstMessage()

        for iter in range(self.iters):
            #Inicializo la suma, los clusters y los tags
            distorsion = 0
            for oper in range(self.opers):
                distorsion += float(self.from_ventilator.recv_string())

            print("Sending to fan")
            
            self.to_ventilator.send_string(str(distorsion))
            self.to_ventilator.recv()

    def __init__(self, dir_sink, dir_ventilator):
        self.dir_sink = dir_sink
        self.dir_ventilator = dir_ventilator
        self.createSockets()

if __name__ == "__main__":
    console = argparse.ArgumentParser()
    console.add_argument("dir_sink", type=str)
    console.add_argument("dir_ventilator", type=str)
    args = console.parse_args()

    sink = Sink(args.dir_sink, args.dir_ventilator)
    sink.listen()