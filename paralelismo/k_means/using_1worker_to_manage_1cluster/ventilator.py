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
3.Los activa enviandoles la operacion y 
    a.la posicion del cluster  para el que deben calcular la distancia 
    de todos los puntos
    b.Los tags y el numero de cluster
     para que agrupen los datos en el cluster y muevan el centroide
     que les corresponde
4.Recibe la nueva posicion 
    a.Los tags de todos los puntos
    b.La nueva posicion de los centroides asi como los puntos 
    que pertenecen a cada cluster del sink 
"""

class Ventilator:

    n_data = 1000
    max_iters = 1000
    random_state = np.random.randint(0, 100)
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
                                centers = self.n_clusters, 
                                random_state=self.random_state)
        
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
        for i in range(self.n_clusters):
            self.to_workers.send_json({
                "operation" : "new_dataset",
                "n_features" : self.n_features,
                "n_data" : self.n_data,
                "n_clusters" : self.n_clusters,
                "random_state" : self.random_state
            })

        self.to_sink.send_json({
            "n_data" : self.n_data,
            "n_clusters" : self.n_clusters,
        })

    def calculateSizes(self):
        sizes = [0] * self.n_clusters
        for tag in self.y:
            sizes[tag] += 1 
        return sizes
    

    def sendCalculateDistance(self):
        #Los workers calculan la distanciade cada punto a un  cluster
        for centroid in self.centroids:
            self.to_workers.send_json({
                "operation" : "distance",
                "centroid" : centroid,
            })

    def sendCalculateCentroids(self, y_new):
        #Mando a los workers a que muevan el centroide
        #y que con los tags armen los clusters
        for index in range(len(self.centroids)):
            self.to_workers.send_json({
                "operation" : "move_centroid",
                "y" : y_new,
                "n_cluster" : index
            })
    
    def createClusters(self):
        clusters = []
        [clusters.append([]) for i in range(self.n_clusters)]
        for (point, tag) in zip(self.x, self.y):
            clusters[tag].append(point)
        return clusters 


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
        empty_cluster = False
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
            
            #Si ningun punto ha cambiado de cluster paro de iterar
            if np.array_equal(self.y, np.asarray(y_new)):
                changing = False
            else:
                self.y = y_new.copy()
                #Volvemos a incializar los clusters hasta que todos 
                # tengan al menos un elemento
                sizes = self.calculateSizes()
                print(sorted(sizes))
                empty_cluster = np.min(sizes) == 0
                if empty_cluster:
                    self.createCentroids(mins_max)
                
            if not empty_cluster:
                #Le envio a los workers los tags para que me separe los
                #puntos y calcule la nueva posicion de cada centroide
                self.sendCalculateCentroids(y_new)

                #Del sink recibo los centroides, en este caso
                #el sink solo pego los mensajes que le llegaron del worker
                msg = self.from_sink.recv_json()
                self.from_sink.send(b" ")
                
                self.centroids = msg["centroids"]

            
            
        clusters = self.createClusters()
        self.showResult(clusters)


            
    def __init__(self, n_clusters, n_features, 
                    my_dir, my_dir_sink, dir_sink):
        self.n_clusters = n_clusters
        self.n_features = n_features
        
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