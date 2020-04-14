import zmq 
import pandas as pd 
import os 
import numpy as np
import argparse 
import csv 


class Ventilator:

    chunk = 100
    datasets_path = os.path.join("/".join(os.getcwd().split("/")[:-1]), "datasets")

    def createSockets(self):
        self.context = zmq.Context()
        self.to_workers = self.context.socket(zmq.PUSH)
        self.to_workers.bind(f"tcp://{self.my_dir}")

        self.to_sink = self.context.socket(zmq.PUSH)
        self.to_sink.connect(f"tcp://{self.dir_sink}")

        self.from_sink = self.context.socket(zmq.REP)
        self.from_sink.bind(f"tcp://{self.my_dir_sink}")

    def normalizeDataset(self):
        name_normalized = self.name_dataset.split(".")[0] + "_normalized.csv"
        iris_col = pd.read_csv(os.path.join(self.datasets_path, 
                                self.name_dataset), nrows = 1).columns

        with open(os.path.join(self.datasets_path, name_normalized), "w") as f:
            writer = csv.writer(f)
            writer.writerow(iris_col)


        input("Press enter when all are ready")
        reading = True
        i  = 0

        #Loop en el que se calcula el promedio de cada caracteristica
        while reading:
            data = pd.read_csv(os.path.join(self.datasets_path, self.name_dataset),
                                skiprows=i, nrows=self.chunk).values
            if self.has_tags:
                data = data[:, :-1]
            reading = len(data) == self.chunk
            if len(data != 0):
                print("Sending data to workers")
                self.to_workers.send_json({
                    "action" : "media",
                    "points" : np.ndarray.tolist(data),
                })
            i += self.chunk
        
        self.to_workers.send_json({
            "action" : "end"
        })

        media = self.from_sink.recv_json()["average_points"]
        self.from_sink.send(b" ")
        print(media)

        i = 0
        reading = True
        #Loop en el que se calcula la desviacion estandar de cada muestra 
        while reading:
            data = pd.read_csv(os.path.join(self.datasets_path, self.name_dataset),
                                skiprows=i, nrows=self.chunk).values
            if self.has_tags:
                data = data[:, :-1]
            reading = len(data) == self.chunk
            if len(data != 0):
                print("Sending data to workers")
                self.to_workers.send_json({
                    "action" : "desvesta",
                    "points" : np.ndarray.tolist(data),
                    "media" : media
                })
            i += self.chunk
        self.to_workers.send_json({
            "action" : "end"
        })
        desvesta = self.from_sink.recv_json()["desvesta"]
        self.from_sink.send_string(name_normalized)
        print(desvesta)


        #Loop en el que se normalizan los datos 
        i = 0
        reading = True
        while reading:
            data = pd.read_csv(os.path.join(self.datasets_path, self.name_dataset),
                                skiprows=i, nrows=self.chunk).values
            
            reading = len(data) == self.chunk
            if len(data != 0):
                print("Sending data to workers")
                self.to_workers.send_json({
                    "action" : "normalize",
                    "points" : np.ndarray.tolist(data),
                    "media" : media,
                    "desvesta" : desvesta,
                    "has_tags" : self.has_tags
                })
            i += self.chunk
        self.to_workers.send_json({
            "action" : "end"
        })
        self.from_sink.recv_string()
        self.from_sink.send(b" ")


    def __init__(self, name_dataset, my_dir, my_dir_sink,  dir_sink, has_tags):
        self.my_dir = my_dir
        self.my_dir_sink = my_dir_sink
        self.dir_sink = dir_sink
        self.name_dataset = name_dataset
        self.has_tags = has_tags
        self.createSockets()




def createConsole():
    console = argparse.ArgumentParser()
    console.add_argument("name_dataset", type=str)
    console.add_argument("my_dir", type=str)
    console.add_argument("my_dir_sink", type=str)
    console.add_argument("dir_sink", type=str)
    console.add_argument("--tags", "-t", action = "store_true")
    return console.parse_args()


if __name__ == "__main__":
    args = createConsole()
    ventilator = Ventilator(args.name_dataset, args.my_dir, args.my_dir_sink, 
                            args.dir_sink, args.tags)
    ventilator.normalizeDataset()