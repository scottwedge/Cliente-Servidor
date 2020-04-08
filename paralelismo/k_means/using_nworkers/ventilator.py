from sklearn.datasets import make_blobs
import numpy as np
from utilsKmeans import *
import zmq
import matplotlib.pyplot as plt
import argparse
"""
En esta aproximacion, el ventilator:
1.Instancia los centroides
2.Llama a los workers como instanciar el dataset
3.Los activa enviandoles la operacion y 
    a.Los puntos para los que deben calcular la distancia a 
    todos los clusters, junto con los clusters

4.Recibe 
    a.Los clusters
    b.La posicion de los centroides
    c.Los tags
"""

class Ventilator:


    def createSockets(self):
        self.context = zmq.Context()

        self.to_workers = self.context.socket(zmq.PUSH)
        self.to_workers.bind(f"tcp://{self.my_dir}")

        self.to_sink = self.context.socket(zmq.PUSH)
        self.to_sink.connect(f"tcp://{self.dir_sink}")

        self.from_sink = self.context.socket(zmq.REP)
        self.from_sink.bind(f"tcp://{self.my_dir_sink}")

    def instanciateDataset(self):
        #Creamos el dataset
        self.x, self.y = make_blobs(n_samples = self.n_data, 
                                n_features=self.n_features, 
                                centers = self.n_clusters)
        
        if self.n_features == 2:
            plt.scatter(self.x[:, 0], self.x[:, 1])
            plt.show()

    def calculateMinMaxFeatures(self):
        #Calcula el minimo y el maximo de cada atributo para asi
        #inicializar el centroide 
        mins_max = []
        for i in range(self.n_features):
            min_f = np.min(self.x[:, i])
            max_f = np.max(self.x[:, i])
            mins_max.append((min_f, max_f))
        return mins_max


    def createCentroids(self, mins_max):
        #Creamos los centroides de manera aleatoria en el rango de cada 
        #caracteristica
        self.centroids = []
        for i in range(self.n_clusters):
            centroid = [] 
            for j, min_max in enumerate(mins_max):
                centroid.append(np.random.uniform(low = min_max[0], high = min_max[1]))
            self.centroids.append(centroid)
        
    def showResult(self, clusters):
        #Muestra los puntos asignados a cada cluster y si el numero de
        #features es de 2, mostrara la grafica
        for i, c in enumerate(clusters):
            print(f"\tCLUSTER{i+1}")
            [print(point) for point in c]
        
        if self.n_features == 2:
            show(clusters, self.centroids)

    def sendInitialData(self):
        #Para no enviarle el dataset en cada iteracion. 
        #data_list = np.ndarray.tolist(self.x)
        # for i in range(self.n_clusters):
        #     self.to_workers.send_json({
        #         "data" : data_list,
        #         "n_features" : self.n_features,
        #         "n_clusters" : self.n_clusters
        #         "position" : []
        #     })

        opers = self.n_data // self.chunk_worker
        if self.n_data % self.chunk_worker != 0:
            opers += 1

        self.to_sink.send_json({
            "n_data" : self.n_data,
            "n_clusters" : self.n_clusters,
            "n_features" : self.n_features,
            "opers" : opers
        })

    def isEmptyCluster(self, clusters):
        #Verificamos si algun cluster quedo vacio
        empty = False
        i = 0
        while not empty and i < len(clusters):
            if len(clusters[i]) == 0:
                print("Empty cluster!")
                empty = True
            i += 1
        return empty
    

    def sendCalculateDistance(self):
        #Los workers calculan la distanciade cada punto a un  cluster
        i = 0
        while i < self.n_data:
            self.to_workers.send_json({
                "centroids" : self.centroids,
                "points" : np.ndarray.tolist(self.x[i: i + self.chunk_worker]),
                "position" : [i, i+self.chunk_worker]
            })
            i += self.chunk_worker
    
    def kmeans(self):
        #Metodo k_means paralelizado.
        input("Press enter when workers are ready")
        self.sendInitialData()
        #Creo los centroides de manera aleatoria en el rango 
        #de cada dimension de los puntos
        mins_max = self.calculateMinMaxFeatures() 
        self.createCentroids(mins_max)

        self.y =  np.zeros(self.n_data)
        changing = True
        iters = 0
        while changing and iters < self.max_iters:
            iters += 1
            print("Operating")

            self.sendCalculateDistance()

            #Del sink recibo los tags
            print("Waiting result from sink")
            result = self.from_sink.recv_json()
            self.from_sink.send(b" ")

            y_new = result["y"]
            clusters = result["clusters"]
            self.centroids = result["centroids"]

            lens = [len(cluster) for cluster in clusters]
            print(sorted(lens))

            #Si ningun punto ha cambiado de cluster paro de iterar
            if np.array_equal(self.y, np.asarray(y_new)):
                changing = False
            else:
                self.y = y_new.copy()
                #Volvemos a incializar los clusters hasta que todos 
                # tengan al menos un elemento
                empty_cluster = self.isEmptyCluster(clusters)
                if empty_cluster:
                    self.createCentroids(mins_max)

        self.showResult(clusters)


            
    def __init__(self, n_clusters, n_features, 
                    my_dir, my_dir_sink, dir_sink):
        self.n_clusters = n_clusters
        self.n_features = n_features

        self.n_data = 1010
        self.max_iters = 1000
        self.chunk_worker = 100

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
    console.add_argument("n_clusters", type=int)
    console.add_argument("n_features", type=int)
    return console.parse_args()

if __name__ == "__main__":
    args = createConsole()
    ventilator = Ventilator(args.n_clusters, args.n_features, 
                            args.my_dir, args.my_dir2, args.dir_sink)
    ventilator.kmeans()