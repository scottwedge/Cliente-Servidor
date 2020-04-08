"""
    En esta implementacion, el sink:
    1.Recoge las distancias a cada cluster de los workers 
    2.Calcula el minimo de las distancias y asigna el punto a un cluster
    5.Calcula la nueva posicion de los centroides
    3.Envia los resultados al ventilator
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


    #Funcion donde le llegara el mensaje del ventilator
    def listen(self):
        print("Ready")
        msg = self.from_ventilator.recv_json()
        self.n_data = msg["n_data"]
        self.n_clusters = msg["n_clusters"]
        print("Recieve first message")

        #Pegando todas las distancias
        while True:
            self.distances = np.zeros((self.n_data, self.n_clusters))
            clusters = []
            centroids = []

            for cluster in range(self.n_clusters):
                print("Waiting message from workers")
                msg = self.from_ventilator.recv_json()
                print("Message from worker recieved")

                if msg["type"] == "distances":
                    
                    distances = np.asarray(msg["distances"])
                    self.distances[:, cluster] = distances
                elif msg["type"] == "clusters":
                    
                    clusters.append(msg["cluster"])
                    centroids.append(msg["centroid"])

            if msg["type"] == "distances":
                print("Calculating tags")
                #Calculando la minima distancia
                y = []
                for i in range(self.n_data):
                    y.append(int(np.argmin(self.distances[i, :])))
                print("Sending data to ventilator")
                self.to_ventilator.send_json({
                    "y" : y,
                })
                
            elif msg["type"] == "clusters":
                print("Appending clusters")
                print("Sending data to ventilator")
                self.to_ventilator.send_json({
                    "clusters" : clusters,
                    "centroids" : centroids
                })
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