from sklearn.datasets import make_blobs
import numpy as np
from utilsKmeans import *
import zmq
import matplotlib.pyplot as plt
import argparse
"""
En esta aproximacion, el ventilator:
1.Instancia los centroides
2.Llama a los workers diciendoles que cluster deben manejar y
  como instanciar el dataset
3.Los activa enviandoles 'operate' y la posicion del cluster
  porque se supone que los workers tienen acceso al dataset
4.Recibe la nueva posicion de los clusters asi como los puntos 
  que pertenecen a cada cluster del sink 
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

    def divideData(self):
        self.clusters = []
        for cluster in range(self.n_clusters):
            self.clusters.append(
                np.array([self.x[i, :] 
                        for i in range(self.n_data) if self.y[i] == cluster]))  


    def instanciateDataset(self):
        self.x, self.y = make_blobs(n_samples = self.n_data, 
                                n_features=self.n_features, 
                                centers = self.n_clusters)
        
        if self.n_features == 2:
            plt.scatter(self.x[:, 0], self.x[:, 1])
            plt.show()

    def calculateMinMaxFeatures(self):
        self.mins_max = []
        for i in range(self.n_features):
            min_f = np.min(self.x[:, i])
            max_f = np.max(self.x[:, i])
            self.mins_max.append((min_f, max_f))


    def createCentroids(self):
        centroids = []
        for i in range(self.n_clusters):
            centroid = [] 
            for j, min_max in enumerate(self.mins_max):
                centroid.append(np.random.uniform(low = min_max[0], high = min_max[1]))
            centroids.append(centroid)
        return centroids


    def sendInitialData(self):
        #Para no enviarle el dataset en cada iteracion. 
        data_list = np.ndarray.tolist(self.x)
        for i in range(self.n_clusters):
            self.to_workers.send_json({
                "data" : data_list,
                "n_features" : self.n_features
            })

        self.to_sink.send_json({
            "n_data" : self.n_data,
            "n_clusters" : self.n_clusters,
        })

    def isEmptyCluster(self, clusters):
        empty = False
        i = 0
        while not empty and i < len(clusters):
            if len(clusters[i]) == 0:
                empty = True
            i += 1
        return empty

    def kmeans(self):
        input("Press enter when workers are ready")
        self.sendInitialData()
        #Creo los centroides de manera aleatoria en el rango 
        #de cada dimension de los puntos
        self.calculateMinMaxFeatures() 
        centroids = self.createCentroids()

        self.y =  np.zeros(self.n_data)
        changing = True
        while changing:
            print("Operating")
            #Calculo la distancia de cada punto a todos los clusters 
            #y lo asigno a un cluster
            for centroid in centroids:
                print("Sending centroids")
                self.to_workers.send_json({
                    "operation" : "distance",
                    "centroid" : centroid,
                })

            #Del sink recibo los tags
            print("Waiting result from sink")
            result = self.from_sink.recv_json()
            self.from_sink.send(b" ")
            y_new = result["y"]


            #Mando a los workers a que muevan el centroide
            for index in range(len(centroids)):
                print("Sending to move")
                self.to_workers.send_json({
                    "operation" : "move_centroid",
                    "y" : y_new,
                    "n_cluster" : index
                })
            msg = self.from_sink.recv_json()
            self.from_sink.send(b" ")
            clusters = msg["clusters"]
            centroids = msg["centroids"]

            #Si ningun punto ha cambiado de cluster paro de iterar
            if np.array_equal(self.y, np.asarray(y_new)):
                changing = False
            else:
                self.y = y_new.copy()
                #Volvemos a incializar los clusters hasta que todos 
                # tengan al menos un elemento
                empty_cluster = self.isEmptyCluster(clusters)
                if empty_cluster:
                    self.createCentroids()

        for i, c in enumerate(clusters):
            print(f"\tCLUSTER{i+1}")
            [print(point) for point in c]
        
        if self.n_features == 2:
            show(clusters, centroids)


            
    def __init__(self, n_clusters, n_features, 
                    my_dir, my_dir_sink, dir_sink):
        self.n_clusters = n_clusters
        self.n_features = n_features
        self.n_data = 1000
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