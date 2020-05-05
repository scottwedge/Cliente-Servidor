import zmq 
import numpy as np 
import pandas as pd
import os 
import argparse
import csv 

class Worker:


    datasets_path = os.path.join("/".join(os.getcwd().split("/")[:-1]), "datasets")


    def createSockets(self):
        self.context = zmq.Context()
        
        self.from_ventilator = self.context.socket(zmq.PULL)
        self.from_ventilator.connect(f"tcp://{self.dir_ventilator}")

        self.to_sink = self.context.socket(zmq.PUSH)
        self.to_sink.connect(f"tcp://{self.dir_sink}")


    def readPartDataset(self, skiprows, returnTags = False):
        data = pd.read_csv(os.path.join(self.datasets_path, self.name_dataset),
                                skiprows=skiprows, nrows=self.chunk).values
        if self.has_tags:
            data_x = data[:, :-1]
        else:
            data_x = data

        if not returnTags:
            return data_x
        
        data_y = np.ndarray.tolist(data[:, -1])
        return data_x, data_y
        
    def receiveInitialData(self, msg):
        print("Initial data received")
        self.name_normalized = msg["name_normalized"]
        self.name_dataset = msg["name_dataset"]
        self.has_tags = msg["has_tags"]
        self.chunk = msg["chunk"]
        
    def sendMedia(self, msg):
        skiprows = msg["skiprows"]
        points = self.readPartDataset(skiprows)
        sum_points = np.ndarray.tolist(np.sum(points, axis = 0))
        n_elements = points.shape[0]
        print("Sending sum to sink")
        self.to_sink.send_json({
            "action" : "media",
            "sum_points" : sum_points, 
            "n_elements" : n_elements
        })

    def sendDesvesta(self, msg):
        skiprows = msg["skiprows"]
        points = self.readPartDataset(skiprows)
        media = np.asarray(msg["media"])
        sum_points = np.sum((points-media)**2, axis = 0)
        sum_points = np.ndarray.tolist(sum_points)
        print("Sending sum desvesta to sink")
        self.to_sink.send_json({
            "action" : "desvesta",
            "sum_points" : sum_points, 
        })
    
    def normalizePoints(self, msg):
        media = np.asarray(msg["media"])
        desvesta = np.asarray(msg["desvesta"])

        skiprows = msg["skiprows"]
        if self.has_tags:
            points, tags = self.readPartDataset(skiprows, returnTags = True)
        else:
            points = self.readPartDataset(skiprows)
        
        points = points.astype(np.float)
        media = media.astype(np.float)
        desvesta = desvesta.astype(np.float)
        points = (points - media)/desvesta

        with open(os.path.join(self.datasets_path, self.name_normalized), "a") as f:
            writer = csv.writer(f)
            if self.has_tags:
                for (p, t) in zip(points, tags):
                    writer.writerow(np.append(p, t))
            else:
                for p in points:
                    writer.writerow(p)

        print("Sending end normalize sink")
        self.to_sink.send_json({
            "action" : "end_normalize",
        })

        

    def listen(self):
        print("ready")
        while True:
            msg = self.from_ventilator.recv_json()
            action = msg["action"]

            if action == "media":
                self.sendMedia(msg)
            elif action == "desvesta":
                self.sendDesvesta(msg)
            elif action == "normalize":
                self.normalizePoints(msg)
            elif action == "new_dataset":
                self.receiveInitialData(msg)


    def __init__(self, dir_ventilator, dir_sink):
        self.dir_ventilator = dir_ventilator
        self.dir_sink = dir_sink
        self.createSockets()




def createConsole():
    console = argparse.ArgumentParser()
    console.add_argument("dir_ventilator", type=str)
    console.add_argument("dir_sink", type=str)
    return console.parse_args()


if __name__ == "__main__":
    args = createConsole()
    worker = Worker(args.dir_ventilator, args.dir_sink)
    worker.listen()
