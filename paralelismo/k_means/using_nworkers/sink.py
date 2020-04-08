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
        self.n_features = msg["n_features"]
        self.opers = msg["opers"]
        print("Recieve first message")

    
        while True:
            #Inicializo la suma, los clusters y los tags
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
                    clusters[i].extend(clusters_temp[i]) #Pego los clusters
                    sum_points[i] += sum_points_temp[i] #Sumo los resultados de cada worker
                    y[ini:fin] = y_temp #Voy armando el vector de tags
                
            #Promedio la suma para encontrar la posicion del centroide
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