"""
    Para esta implementacion, cada worker:
    1.Calcula la distancia del los que le llegaron puntos a 
      todos los centroides
    2.Con esta distancia saca el vector de tags y los clusters para
    el numero determinado de puntos 
"""
import zmq
import argparse 
from scipy.spatial import distance
import numpy as np
from sklearn.datasets import make_blobs
import pandas as pd
from os.path import join 

class Worker:

    def instanciateDataset(self, has_tags):
        #Abre el dataset con la ayuda de pandas
        data = pd.read_csv(join("datasets", self.name_dataset))
        if has_tags:
            self.x = data.values[:, :-1]
        else:
            self.x = data.values
        self.x = self.x.astype(np.float)
        self.n_data, self.n_features = self.x.shape

    def recieveInitialData(self, msg):
        #Por ahora no se usa, ya que como no se cuantos workers tengo
        #no puedo enviar el data set al inicio
        self.name_dataset = msg["name_dataset"]
        self.n_clusters = msg["n_clusters"]
        print("Recieved first message")
        self.instanciateDataset(msg["has_tags"])


    def calculateDistances(self, centroids):
        #Calcula la distancia entre todos los puntos y un centroide dado
        #Matriz de tamanio data * centroids
        
        points = self.x[self.min : self.max]
        distances = []
        for p in (points):
            distance_point = []
            for centroid in centroids:
                distance_point.append(distance.euclidean(p, centroid))
            distances.append(distance_point)
        return distances
    
    
    def calculateTagsAndSum(self, distances):
        #A partir de las distancias anteriormente calculadas, crea 
        #los clusters y los tags, ademas de sumar los puntos de cada
        #cluster para que luego el sink los pueda promediar
        print("Calculating tags, clusters and sum")
        y = []
        #Inicializo los clusters vacios
        sum_points = np.zeros((self.n_clusters, self.n_features))
        index = 0
        for i in range(self.min, self.max):
            index_min = int(np.argmin(distances[index]))
            y.append(index_min) #Tags
            sum_points[index_min] += self.x[i] #Suma de los puntos
            index += 1
        return (y, sum_points)


            
    def listen(self): 
        print("Ready")
        while True:
            msg = self.from_ventilator.recv_json()
            if msg["action"] == "new_dataset":
                    self.recieveInitialData(msg)
            else:

                self.min, self.max = msg["position"]
        
                print("Calculating distance")
                centroids = msg["centroids"]

                distances = self.calculateDistances(centroids)
                tags, sum_points = self.calculateTagsAndSum(distances)
                self.to_sink.send_json({
                    "tags" : tags,
                    "sum_points" : np.ndarray.tolist(sum_points), 
                    "position" : [self.min, self.max]
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