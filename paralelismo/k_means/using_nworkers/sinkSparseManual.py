"""
    Solo cambia que la suma de los puntos es una matriz dispersa 
    y la forma de enviar el mensaje en el json

"""

import zmq 
import numpy as np
import argparse
from utils import sumDictAndPoint, sumPointsDict
class Sink:

    #Crea el socket donde le llega la informacion del 
    #ventilator, que son el numero de clusters
    def createSockets(self):
        self.context = zmq.Context()

        self.from_ventilator = self.context.socket(zmq.PULL)
        self.from_ventilator.bind(f"tcp://{self.dir_sink}")

        self.to_ventilator = self.context.socket(zmq.REQ)
        self.to_ventilator.connect(f"tcp://{self.dir_ventilator}")

    def receiveFirstMessage(self):
        msg = self.from_ventilator.recv_json()
        self.n_clusters = msg["n_clusters"]
        self.n_data = msg["n_data"]
        self.n_features = msg["n_features"]
        self.opers = msg["opers"]
        self.chunk = msg["chunk"]
        print("Receive first message")

    def calculateSizeClusters(self, y):
        sizes = [0] * self.n_clusters
        for tag in y:
            sizes[tag] += 1
        return sizes 

    #Funcion donde le llegara el mensaje del ventilator
    def listen(self):
        print("Ready")

        #Este primer while true me servira para no tener que interrumpir 
        #el sink cada vez que quiero hacer un nuevo k means, asi podra 
        #recibir la data inicial y volver a empezar
        while True:
            self.receiveFirstMessage()

            #Lo meto en un while true porque no se cuantas iteraciones puede 
            #llegar a realizar kmeans, por lo que siempre debe estar 
            #disponible
            end = False
            while not end:
                #Inicializo la suma, los clusters y los tags
                sum_points = []
                for i in range(self.n_clusters):
                    sum_points.append({})

                y = [0] * self.n_data

                for oper in range(self.opers):
                    msg = self.from_ventilator.recv_json()
                    print("Msg received from worker")
                    y_temp = msg["tags"]
                    sum_points_temp = msg["sum_points"]
                    ini = msg["position"]

                    fin = ini + self.chunk
                    if fin > self.n_data:
                        fin = self.n_data

                    y[ini:fin] = y_temp.copy() #Voy armando el vector de tags
                    for i in range(self.n_clusters):
                        print("Adding points")
                        #Sumo los resultados de cada worker
                        sum_points[i] = sumPointsDict(sum_points[i], sum_points_temp[i])
                            
                
                sizes = self.calculateSizeClusters(y)
                #Promedio la suma para encontrar la posicion del centroide
                for i, size in enumerate(sizes):
                    if size != 0:
                        for key in sum_points[i].keys():
                            sum_points[i][key] = sum_points[i][key] / size

                print("Sending to fan")
                
                self.to_ventilator.send_json({
                    #"centroids" : np.ndarray.tolist(sum_points),
                    "centroids" : sum_points,
                    "y" : y,
                    "sizes" : sizes
                })
                end = self.to_ventilator.recv_string() == "end"

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
