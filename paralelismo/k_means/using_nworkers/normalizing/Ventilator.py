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


    def sendInitialData(self):
        opers = self.n_data // self.chunk
        if self.n_data % self.chunk != 0:
            opers += 1
        self.to_sink.send_json({
            "n_data" : self.n_data,
            "opers" : opers
        })
        
        i = 0
        while i <= self.n_data:
            print("Sending data to workers")
            self.to_workers.send_json({
                "action" : "new_dataset",
                "name_normalized" : self.name_normalized, 
                "name_dataset" : self.name_dataset,
                "has_tags" : self.has_tags,
                "chunk" : self.chunk
            })
            i += self.chunk

    def sendCalculateMedia(self):
        i = 0
        while i <= self.n_data:
            print("Sending data to workers")
            self.to_workers.send_json({
                "action" : "media",
                "skiprows" : i,
            })
            i += self.chunk
        
        self.to_workers.send_json({
            "action" : "end"
        })

        media = self.from_sink.recv_json()["average_points"]
        self.from_sink.send(b" ")
        print(media)
        return media 


    def sendCalculateDesvesta(self, media):
        i = 0
        #Loop en el que se calcula la desviacion estandar de cada muestra 
        while i <= self.n_data:
            print("Sending data to workers")
            self.to_workers.send_json({
                "action" : "desvesta",
                "skiprows" : i,
                "media" : media
            })
            i += self.chunk
        self.to_workers.send_json({
            "action" : "end"
        })
        desvesta = self.from_sink.recv_json()["desvesta"]
        self.from_sink.send(b" ")
        print(desvesta)
        return desvesta 


    def sendNormalizeData(self, media, desvesta):
        #Loop en el que se normalizan los datos 
        i = 0
        while i <= self.n_data:
            print("Sending data to workers")
            self.to_workers.send_json({
                "action" : "normalize",
                "skiprows" : i,
                "media" : media,
                "desvesta" : desvesta,
                "has_tags" : self.has_tags
            })
            i += self.chunk
        self.from_sink.recv_string()
        self.from_sink.send(b" ")

    def normalizeDataset(self):
        self.name_normalized = self.name_dataset.split(".")[0] + "_normalized.csv"
        cols = pd.read_csv(os.path.join(self.datasets_path, 
                                self.name_dataset), nrows = 1).columns

        with open(os.path.join(self.datasets_path, self.name_normalized), "w") as f:
            writer = csv.writer(f)
            writer.writerow(cols)


        input("Press enter when all are ready")

        self.sendInitialData()
        #Loop en el que se calcula el promedio de cada caracteristica
        media = self.sendCalculateMedia()
        #Loop en el que se calcula la desviacion estandar 
        desvesta = self.sendCalculateDesvesta(media)
        #Loop en el que se normalizan los datos 
        self.sendNormalizeData(media, desvesta)


    def __init__(self, name_dataset, my_dir,  my_dir_sink, 
                 dir_sink, n_data, has_tags):
        self.my_dir = my_dir
        self.n_data = n_data
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
    console.add_argument("dir_sink", type = str)
    console.add_argument("n_data", type=int)
    console.add_argument("--tags", "-t", action = "store_true")
    return console.parse_args()


if __name__ == "__main__":
    args = createConsole()
    ventilator = Ventilator(args.name_dataset, args.my_dir, 
                            args.my_dir_sink, args.dir_sink,
                            args.n_data, args.tags)
    ventilator.normalizeDataset()