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
class Worker:

    def recieveInitialData(self):
        #Por ahora no se usa, ya que como no se cuantos workers tengo
        #no puedo enviar el data set al inicio
        msg = self.from_ventilator.recv_json()
        self.data = np.asarray(msg["data"])
        self.n_features = msg["n_features"]
        self.n_clusters = msg["n_clusters"]
        print("Recieved first message")
        self.n_data = self.data.shape[0]


    def calculateDistances(self, centroids, points):
        #Calcula la distancia entre todos los puntos y un centroide dado
        #Matriz de tamanio data * centroids
        distances = []
        for p in points:
            distance_point = []
            for centroid in centroids:
                distance_point.append(distance.euclidean(p, centroid))
            distances.append(distance_point)
        return distances
    
    
    def calculateTagsAndSum(self, distances, points, n_clusters):
        #A partir de las distancias anteriormente calculadas, crea 
        #los clusters y los tags, ademas de sumar los puntos de cada
        #cluster para que luego el sink los pueda promediar

        n_features = points.shape[1]
    
        print("Calculating tags, clusters and sum")
        y = []
        #Inicializo los clusters vacios
        clusters = []
        [clusters.append([]) for i in range(n_clusters)]
        sum_points = np.zeros((n_clusters, n_features))

        for i in range(len(points)):
            index_min = int(np.argmin(distances[i]))
            y.append(index_min) #Tags
            sum_points[index_min] += points[i] #Suma de los puntos
            clusters[index_min].append(np.ndarray.tolist(points[i])) #Puntos del cluster

        return (y, clusters, sum_points)

    def listen(self): 
        print("Ready")
        #Ciclo en el que recibe los dos arrays y los multiplica
        #self.recieveInitialData()
        while True:
            msg = self.from_ventilator.recv_json()
            print("Calculating distance")
            points_to_work = np.asarray(msg["points"]) #Puntos a trabajar
            min_pos, max_pos = msg["position"] #Posiciones para luego armar bien el 
                                               # vector de tags
            centroids = msg["centroids"]
 
            distances = self.calculateDistances(centroids, 
                                                points_to_work)

            tags, clusters, sum_points = (
                    self.calculateTagsAndSum(distances, points_to_work, len(centroids)))

            self.to_sink.send_json({
                "tags" : tags,
                "sum_points" : np.ndarray.tolist(sum_points), 
                "clusters" : clusters,
                "position" : [min_pos, max_pos]
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