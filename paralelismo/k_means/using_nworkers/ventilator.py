from sklearn.datasets import make_blobs
import numpy as np
from utilsKmeans import *
import zmq
import matplotlib.pyplot as plt
import argparse
import time
import pandas as pd 
from os.path import join
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

    n_data = 1932
    max_iters = 1000
    chunk_worker = 10
    random_state  = np.random.randint(0, 100)
    #random_state  = 10


    def createSockets(self):
        self.context = zmq.Context()

        self.to_workers = self.context.socket(zmq.PUSH)
        self.to_workers.bind(f"tcp://{self.my_dir}")

        self.to_sink = self.context.socket(zmq.PUSH)
        self.to_sink.connect(f"tcp://{self.dir_sink}")

        self.from_sink = self.context.socket(zmq.REP)
        self.from_sink.bind(f"tcp://{self.my_dir_sink}")

    

    def readPartDataset(self, i):
        data = pd.read_csv(join("datasets", self.name_dataset), 
                            skiprows=i, nrows=self.chunk_worker)
        if self.has_tags:
            values = data.values[:, :-1]
        else:
            values = data.values        
        reading = values.shape[0] == self.chunk_worker
        return values, reading 


    def instanciateDataset(self):
        #Abre el dataset con la ayuda de pandas
        self.n_data = 0
        i = 0
        reading = True
        while reading:
            values, reading = self.readPartDataset(i)
            if i == 0:
                self.n_features = values.shape[1]

            self.n_data += values.shape[0]
            if reading and self.n_features == 2:
                plt.scatter(values[:, 0], values[:, 1], c = "salmon")
            i += self.chunk_worker
        plt.show()

    def createCentroids(self):
        #Creamos los centroides de manera aleatoria en el rango de cada 
        #caracteristica
        self.centroids = []
        for i in range(self.n_clusters):
            number = np.random.randint(0, high=self.n_data)
            value = pd.read_csv(join("datasets", self.name_dataset), 
                                skiprows=number, nrows=1).values
            if self.has_tags:
                value = value[:, :-1]
            value = np.ndarray.tolist(value.astype(float))
            self.centroids.append(value)
        
    def showResult(self):
        #Muestra los puntos asignados a cada cluster y si el numero de
        #features es de 2, mostrara la grafica
        for i, c in enumerate(self.clusters):
            print(f"\tCLUSTER{i+1}")
            [print(point) for point in c]
        
        if self.n_features == 2:
            show(self.clusters, self.centroids)

    def sendInitialData(self):
        i = 0 
        #Para no enviarle el dataset en cada iteracion. 
        while i < self.n_data:
            self.to_workers.send_json({
                "action" : "new_dataset",
                "name_dataset" : self.name_dataset,
                "n_clusters" : self.n_clusters,
                "n_features" : self.n_features,
                "has_tags" : self.has_tags,
                "chunk" : self.chunk_worker
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
            "chunk" : self.chunk_worker
        })

    def sendCalculateDistance(self):
        #Los workers calculan la distancia de un numero determinado
        # de puntos punto a todos los  cluster
        i = 0
        while i < self.n_data:
            i_max = i + self.chunk_worker 
            if i_max > self.n_data:
                i_max = self.n_data
            self.to_workers.send_json({
                "action" : "operate",
                "centroids" : self.centroids, 
                "position" : i
            })
            i += self.chunk_worker
    
    def createClusters(self):
        self.clusters = []
        [self.clusters.append([]) for i in range(self.n_clusters)]

        i = 0
        reading = True
        while reading:
            data, reading = self.readPartDataset(i)
            if len(data) != 0:
                for j in range(len(data)):
                    self.clusters[self.y[i+j]].append(data[j])
            i += self.chunk_worker

    def kmeans(self):
        #Metodo k_means paralelizado.
        input("Press enter when workers are ready")
        self.sendInitialData()
        #Creo los centroides de manera aleatoria en el rango 
        #de cada dimension de los puntos
        self.createCentroids()

        self.y =  np.zeros(self.n_data)
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
            self.from_sink.send(b" ")

            size_clusters = result["sizes"]
            y_new = result["y"]
            self.centroids = result["centroids"]

            print(sorted(size_clusters))

            #Si ningun punto ha cambiado de cluster paro de iterar
            if np.array_equal(self.y, np.asarray(y_new)):
                changing = False
            else:
                self.y = y_new.copy()

        print("END")
        self.createClusters()
        self.showResult()
    


            
    def __init__(self, name_dataset, has_tags, 
                    my_dir, my_dir_sink, dir_sink, n_clusters):
        self.name_dataset = name_dataset
        self.n_clusters = n_clusters
        self.has_tags = has_tags
        self.instanciateDataset()
        
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
    console.add_argument("n_clusters", type=int)
    console.add_argument("-t", "--tags", action="store_true")
    return console.parse_args()

if __name__ == "__main__":
    args = createConsole()
    ventilator = Ventilator(args.name_file, args.tags,  args.my_dir, 
                            args.my_dir2, args.dir_sink, args.n_clusters)
    ventilator.kmeans()