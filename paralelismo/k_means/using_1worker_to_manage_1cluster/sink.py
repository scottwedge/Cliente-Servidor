"""
    En esta implementacion, el sink:
    1.Recoge las distancias a cada cluster de los workers 
    3.Calcula la distancia minima de cada punto a cada cluster y 
    se lo envia al ventilator
    2.Recoge los clusters y los centroides de los workers y los pega para
    enviarselos al ventilator
"""

import zmq 
import numpy as np
import argparse
import time
class Sink:

    #Crea el socket donde le llega la informacion del 
    #ventilator, que son el numero de clusters
    def createSockets(self):
        self.context = zmq.Context()

        self.from_ventilator = self.context.socket(zmq.PULL)
        self.from_ventilator.bind(f"tcp://{self.dir_sink}")

        self.to_ventilator = self.context.socket(zmq.REQ)
        self.to_ventilator.connect(f"tcp://{self.dir_ventilator}")

    def sendTags(self, distances):
        print("Calculating tags")
        #Calculando la minima distancia
        y = []
        for i in range(self.n_data):
            y.append(int(np.argmin(distances[i, :])))
        self.to_ventilator.send_json({
            "y" : y,
        })

    def sendCentroids(self, centroids):
        print("Appending centroids")
        self.to_ventilator.send_json({
            "centroids" : centroids
        })


    #Funcion donde le llegara el mensaje del ventilator
    def listen(self):
        print("Ready")
        msg = self.from_ventilator.recv_json()
        self.n_data = msg["n_data"]
        self.n_clusters = msg["n_clusters"]
        print("Recieve first message")

        #Pegando todas las distanciasy calculando el minimo
        # O pegando los clusters y centroides
        while True:
            distances = np.zeros((self.n_data, self.n_clusters))
            centroids = []
            for cluster in range(self.n_clusters):
                msg = self.from_ventilator.recv_json()

                if msg["type"] == "distances":
                    distance = np.asarray(msg["distances"])
                    distances[:, cluster] = distance
                elif msg["type"] == "clusters":
                    centroids.append(msg["centroid"])

            if msg["type"] == "distances":
                self.sendTags(distances)   
            elif msg["type"] == "clusters":
                self.sendCentroids(centroids)
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