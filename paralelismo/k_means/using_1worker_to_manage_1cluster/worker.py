"""
    Para esta implementacion, cada worker:
    1.Calcula la distancia del todos los puntos a un centroide
"""
import zmq
import argparse 
from scipy.spatial import distance
import numpy as np
class Worker:

    def calculateDistances(self, centroid):
        distances = []
        for i in range(self.n_data):
            distances.append(distance.euclidean(self.data[i], centroid))
        return distances


    def createCluster(self, y, n_cluster):
        return [np.ndarray.tolist(self.data[i]) for i in range(self.n_data) if y[i] == n_cluster]
        

    def moveCentroid(self, cluster):
        if len(cluster) != 0:
            centroid = np.ndarray.tolist((np.average(cluster, axis = 0)))
        else:
            centroid = [0]*self.n_features
        return centroid


    def listen(self): 
        print("Ready")
        #Ciclo en el que recibe los dos arrays y los multiplica
        msg = self.from_ventilator.recv_json()
        self.data = np.asarray(msg["data"])
        self.n_features = msg["n_features"]
        print("Recieved first message")
        self.n_data = self.data.shape[0]
        while True:
            print("Waiting message from ventilator")
            msg = self.from_ventilator.recv_json()
            oper = msg["operation"]


            if oper == "distance":
                print("Calculating distance")
                centroid = msg["centroid"]
                print(centroid)
                distances = self.calculateDistances(centroid)
                
                print("Sending data to sink")
                self.to_sink.send_json({
                    "type" : "distances",
                    "distances" : distances,
                })

            elif oper == "move_centroid":
                print("Moving centroid")
                y = msg["y"]
                n_cluster = msg["n_cluster"]
                cluster = self.createCluster(y, n_cluster)
                #Muevo los centroides a la media de los puntos que le pertenecen
                centroid = self.moveCentroid(cluster)
                print("Sending data to sink")
                self.to_sink.send_json({
                    "type" : "clusters",
                    "centroid" : centroid,
                    "cluster" : cluster
                })
    def createSockets(self):
        self.context = zmq.Context()

        self.from_ventilator = self.context.socket(zmq.PULL)
        self.from_ventilator.connect(f"tcp://{self.dir_ventilator}")

        self.to_sink = self.context.socket(zmq.PUSH)
        self.to_sink.connect(f"tcp://{self.dir_sink}")

    def __init__(self, dir_ventilator, dir_sink):
        self.dir_ventilator = dir_ventilator
        self.dir_sink = dir_sink
        self.createSockets()


if __name__ == "__main__":
    console = argparse.ArgumentParser()
    console.add_argument("dir_ventilator", type = str)
    console.add_argument("dir_sink", type = str)
    args = console.parse_args()

    worker = Worker(args.dir_ventilator, args.dir_sink)
    worker.listen()