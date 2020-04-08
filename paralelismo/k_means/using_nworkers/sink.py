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

    def moveCentroid(self, cluster):
        #Mueve el centroide al promedio de los puntos pertenecientes al cluster
        if len(cluster) != 0:
            centroid = np.ndarray.tolist((np.average(cluster, axis = 0)))
        else:
            centroid = [0]*self.n_features
        return centroid

    def sendClustersAndCentroids(self, clusters, centroids):
        print("Appending clusters")
        self.to_ventilator.send_json({
            "clusters" : clusters,
            "centroids" : centroids
        })


    #Funcion donde le llegara el mensaje del ventilator
    def listen(self):
        print("Ready")
        msg = self.from_ventilator.recv_json()
        self.n_data = msg["n_data"]
        self.n_clusters = msg["n_clusters"]
        self.n_features = msg["n_features"]
        self.opers = msg["opers"]
        print("Recieve first message")

        #Pegando todas las distanciasy calculando el minimo
        # O pegando los clusters y centroides
        while True:
            sum_points = np.zeros((self.n_clusters, self.n_features))
            clusters = []
            [clusters.append([]) for i in range(self.n_clusters)]
            y = [0] * self.n_data
            for oper in range(self.opers):
                msg = self.from_ventilator.recv_json()
                y_temp = msg["tags"]
                sum_points_temp = msg["sum_points"]
                clusters_temp = msg["clusters"]
                ini, fin = msg["position"]
                for i in range(self.n_clusters):
                    clusters[i].extend(clusters_temp[i])
                    sum_points[i] += sum_points_temp[i]
                    y[ini:fin] = y_temp
                

            for i in range(self.n_clusters):
                if len(clusters[i]) != 0:
                    sum_points[i] = sum_points[i] / len(clusters[i])

            print("Sending to fan")
            self.to_ventilator.send_json({
                "clusters" : clusters,
                "centroids" : np.ndarray.tolist(sum_points),
                "y" : y
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