"""
    Solo cambia las funciones de distancia y la forma de abrir 
    el dataset, la suma de los puntos ahora tambien es una matriz
    dispersa 
"""
import zmq
import argparse 
from scipy.spatial import distance
from scipy.sparse import csr_matrix, lil_matrix, csc_matrix
import numpy as np
from sklearn.datasets import make_blobs
import pandas as pd
from os.path import join 
from utils import *
import time 

class Worker:

    def readPartDataset(self, ini):
        data = readChunkSparse(self.chunk, ini, self.name_dataset, 
                                self.n_features, dtype = np.int8)
  
        return data

    def receiveInitialData(self, msg):
        #Por ahora no se usa, ya que como no se cuantos workers tengo
        #no puedo enviar el data set al inicio
        self.name_dataset = msg["name_dataset"]
        self.n_clusters = msg["n_clusters"]
        self.n_features = msg["n_features"]
        self.chunk = msg["chunk"]
        self.distance_metric = msg["distance_metric"]
        print("Received first message")
        self.has_tags  = msg["has_tags"]

    def calculateTagsAndSum(self, centroids, points):
        #Calcula la distancia entre unos puntos y todos los centroides, con esto
        #saca la el cluster mas acercado para asi construir el vector de tags y 
        #la suma de los puntos de cada cluster
        #Matriz de tamanio data * centroids
        y = []
        sum_points = lil_matrix((self.n_clusters, self.n_features))
        init_time = time.time()
        for p in (points):
            distance_point = []
            for centroid in centroids:
                if self.distance_metric == "euclidean":
                    distance_point.append(cuadraticEuclideanDistanceSparse(p, centroid))
                elif self.distance_metric == "angular":
                    distance_point.append(cosineSimilarityForSparse(p, centroid))
                    #distance_point.append(cosineSimilarityForSparse2(p, centroid))

            #A partir de las distancias anteriormente calculadas, crea 
            #los tags, ademas de sumar los puntos de cada
            #cluster para que luego el sink los pueda promediar
            index_min = int(np.argmin(distance_point))
            y.append(index_min) #Tags
            sum_points[index_min] += p #Suma de los puntos
        print(f"Time {time.time()-init_time}")
        return  (y, sum_points)
            
    def listen(self): 
        print("Ready")
        while True:
            msg = self.from_ventilator.recv_json()
            action = msg["action"]
            if action == "new_dataset":
                    self.receiveInitialData(msg)
            elif action == "operate":
                ini = msg["position"]

                
                print("Calculating tags and sum")
                centroids = csc_matrix(np.asarray(msg["centroids"]))

                points = self.readPartDataset(ini)
                tags, sum_points = self.calculateTagsAndSum(centroids, points)

                self.to_sink.send_json({
                    "tags" : tags,
                    "sum_points" : np.ndarray.tolist(sum_points.toarray()), 
                    "position" : ini
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
