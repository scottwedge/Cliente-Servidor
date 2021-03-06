from sklearn.datasets import make_blobs
import numpy as np
import zmq
import matplotlib.pyplot as plt
import argparse
import time
import pandas as pd 
from os.path import join
import csv 
import scipy.sparse as sparse
from matplotlib.colors import TABLEAU_COLORS
import json
import linecache
from utils import readSparseManual
"""
En esta aproximacion, el ventilator:
1.Instancia los centroides
2.Llama a los workers como instanciar el dataset
3.Los activa enviandoles la operacion y 
    a.Los puntos para los que deben calcular la distancia a 
    todos los clusters, junto con los centroides

4.Recibe 
    a.Los clusters
    b.La posicion de los centroides
    c.Los tags
"""

class Ventilator:
    max_iters = 100000
    chunk_worker = 100
    tolerance = 0.01

    def createSockets(self):
        self.context = zmq.Context()

        self.to_workers = self.context.socket(zmq.PUSH)
        self.to_workers.bind(f"tcp://{self.my_dir}")

        self.to_sink = self.context.socket(zmq.PUSH)
        self.to_sink.connect(f"tcp://{self.dir_sink}")

        self.from_sink = self.context.socket(zmq.REP)
        self.from_sink.bind(f"tcp://{self.my_dir_sink}")

    def closeSockets(self):
        self.to_workers.unbind(f"tcp://{self.my_dir}")
        self.to_sink.disconnect(f"tcp://{self.dir_sink}")
        self.from_sink.unbind(f"tcp://{self.my_dir_sink}")

    def readPartDataset(self, i):
        #Lee una parte del dataset desde un 'i' dado, 
        #si ya no existen mas datos indica que no hay mas que hacer
        data = pd.read_csv(join("datasets", self.name_dataset), 
                            skiprows=i, nrows=self.chunk_worker)
        if self.has_tags:
            values = data.values[:, :-1]
        else:
            values = data.values        
        reading = values.shape[0] == self.chunk_worker
        return values, reading 


    def createCentroids(self):
        #Creamos los centroides de manera aleatoria en el rango de cada 
        #caracteristica
        self.centroids = []
        for i in range(self.n_clusters):
            number = np.random.randint(1, high=self.n_data-1)

            with open(join("datasets", self.name_dataset), "r") as f:
                for i in range(number):
                    f.readline()
                value = f.readline()

            if self.name_dataset == "netflix-prize-data/netflix2.txt" or \
                self.name_dataset == "netflix-prize-data/netflix2_little.txt":
                #centroid = [0] * self.n_features
                value = json.loads(value[:-1])
                # for key in value.keys():
                #     centroid[int(key)] = value[key]
                # value = centroid.copy()
            else:
                value = np.fromstring(value, sep = ",")
                if self.has_tags:
                    value = value[:-1]
                value = np.ndarray.tolist(value)

            self.centroids.append(value)
    

    def showResult(self):
        #Si tiene dos caracteristicas, abre el dataset por partes y lo 
        #muestra solo al final 

        colors = []
        for color in list(TABLEAU_COLORS):
            colors.append(color.split(":")[-1])
        reading = True 
        i = 0
        while reading:
            data, reading = self.readPartDataset(i)
            
            if reading:
                for j, p in enumerate(data):
                    color = colors[(self.y[i + j] + 1) % len(colors)]
                    plt.scatter(p[0], p[1], c = color)
            i += self.chunk_worker

        for c in self.centroids:
            plt.scatter(c[0], c[1], c = "black", marker = "D")
        
        plt.show()
            
    def sendInitialData(self):
        i = 0 
        #Para no enviarle el dataset en cada iteracion, se le envia el nombre
        #que ellos deben abrir 
        while i < self.n_data:
            self.to_workers.send_json({
                "action" : "new_dataset",
                "name_dataset" : join("datasets", self.name_dataset),
                "n_clusters" : self.n_clusters,
                "n_features" : self.n_features,
                "has_tags" : self.has_tags,
                "chunk" : self.chunk_worker,
                "distance_metric" : self.distance_metric
            })
            i += self.chunk_worker

        #Calculando el numero de operaciones que se haran
        #para decirle al sink lo que debe esperar
        opers = self.n_data // self.chunk_worker
        if self.n_data % self.chunk_worker != 0:
            opers += 1

        self.to_sink.send_json({
            "n_clusters" : self.n_clusters,
            "n_features" : self.n_features, 
            "n_data" : self.n_data, 
            "opers" : opers,
            "chunk" : self.chunk_worker,
        })

    def sendCalculateDistance(self):
        #Los workers calculan la distancia de un numero determinado
        # de puntos punto a todos los  cluster
        i = 0
        while i < self.n_data:
            self.to_workers.send_json({
                "action" : "operate",
                "centroids" : self.centroids, 
                "position" : i
                
            })
            i += self.chunk_worker
    
    def writeTags(self):
        #Escribe el vector y en un nuevo csv 
        name_result = (self.name_dataset.split(".")[0] +
                        f"_result{self.n_clusters}c.csv")
        print("Saved in", name_result)
        with open(join("datasets", "results", name_result), 'w') as f:
            f.write("tag\n")
            for tag in self.y:
                f.write(str(tag)+"\n")
            

    def kmeans(self):
        #Metodo k_means paralelizado.
        
        i = 3
        while i > 0:
            print(f"Starting in {i} sec")
            time.sleep(1)
            i -= 1

        self.sendInitialData()
        #Creo los centroides de manera aleatoria en el rango 
        #de cada dimension de los puntos
        self.createCentroids()

        self.y =  np.zeros(self.n_data, dtype = np.int8)
        changing = True
        iters = 0
        while changing and iters < self.max_iters:
            iters += 1
            print("Iters", iters)
            print("Operating")

            self.sendCalculateDistance()

            #Del sink recibo los tags, los clusters y los 
            #centroides
            print("Waiting result from sink")
            result = self.from_sink.recv_json()
            

            size_clusters = result["sizes"]
            y_new = result["y"]
            self.centroids = result["centroids"]

            print(sorted(size_clusters))

            falses = np.equal(self.y, np.asarray(y_new))
            falses = np.sum(np.where(falses == False, 1, 0))
            #Si ningun punto ha cambiado de cluster paro de iterar
            if falses/self.n_data < self.tolerance:
                changing = False
                self.from_sink.send_string("end")
            else:
                self.from_sink.send_string("continue")
                if np.min(size_clusters) == 0:
                    print("EMPTY CLUSTER")
                    self.createCentroids()
                self.y = y_new.copy()

        print("END")
        self.writeTags()

        if self.n_features == 2:
            self.showResult()
        
        self.closeSockets()
    
    def __init__(self, name_dataset, has_tags, my_dir, 
                    my_dir_sink, dir_sink, n_data, n_features, 
                    n_clusters, distance_metric):

        self.name_dataset = name_dataset
        self.distance_metric = distance_metric
        self.n_clusters = n_clusters
        self.has_tags = has_tags
        self.n_data = n_data
        self.n_features = n_features

        self.my_dir = my_dir
        self.my_dir_sink = my_dir_sink
        self.dir_sink = dir_sink
        self.createSockets()



def createConsole():
    console = argparse.ArgumentParser()
    console.add_argument("my_dir", type=str)
    console.add_argument("my_dir2", type=str)
    console.add_argument("dir_sink", type=str)
    console.add_argument("name_file", type=str)
    console.add_argument("n_data", type=int)
    console.add_argument("n_features", type=int)
    console.add_argument("n_clusters", type=int)
    console.add_argument("distance_metric", type=str)
    console.add_argument("-t", "--tags", action="store_true")
    return console.parse_args()

if __name__ == "__main__":
    args = createConsole()
    ventilator = Ventilator(args.name_file, args.tags,
                            args.my_dir, args.my_dir2, args.dir_sink, 
                            args.n_data, args.n_features, args.n_clusters,  
                            args.distance_metric)
    ventilator.kmeans()