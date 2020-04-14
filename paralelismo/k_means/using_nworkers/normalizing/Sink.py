import numpy as np 
import pandas as pd 
import zmq
import argparse
import os 
import csv

class Sink:



    datasets_path = os.path.join("/".join(os.getcwd().split("/")[:-1]), "datasets")


    def createSockets(self):
        self.context = zmq.Context()
        self.reciever = self.context.socket(zmq.PULL)
        self.reciever.bind(f"tcp://{self.my_dir}")
        
        self.to_ventilator = self.context.socket(zmq.REQ)
        self.to_ventilator.connect(f"tcp://{self.dir_ventilator}")
        

    def listen(self):
        media = True
        average_points = None
        n_elements = 0
        print("ready")
        while media:
            
            msg = self.reciever.recv_json()
            print("Recieved msg  media from worker")
            media = msg["action"] == "media"
            if media:
                if average_points is None:
                    average_points = np.asarray(msg["sum_points"])
                else:
                    average_points +=  np.asarray(msg["sum_points"])
                n_elements += msg["n_elements"]

        average_points = average_points / n_elements
        print("Sending msg to ventilator")
        self.to_ventilator.send_json({
            "average_points" : np.ndarray.tolist(average_points)
        })
        self.to_ventilator.recv()
        
        desvesta_iter = True 
        desvesta = None

        while desvesta_iter:
            msg = self.reciever.recv_json()
            print("Recieved msg desvesta from worker")
            desvesta_iter = msg["action"] == "desvesta"
            if desvesta_iter:
                if desvesta is None:
                    desvesta = np.asarray(msg["sum_points"])
                else:
                    desvesta +=  np.asarray(msg["sum_points"])

        desvesta = np.sqrt(desvesta / n_elements)
        print("Sending msg to ventilator")
        self.to_ventilator.send_json({
            "desvesta" : np.ndarray.tolist(desvesta)
        })
        name_normalized = self.to_ventilator.recv_string()


        new_dataset = True 
        while new_dataset:
            msg = self.reciever.recv_json()
            print("Recieved msg desvesta from worker")
            new_dataset = msg["action"] == "normalize"
            if new_dataset:
                points = np.asarray(msg["points"])
                has_tags = msg["has_tags"]
                if has_tags:
                    tags = np.asarray(msg["tags"])

                with open(os.path.join(self.datasets_path, name_normalized), "a") as f:
                    writer = csv.writer(f)
                    if has_tags:
                        for (p, t) in zip(points, tags):
                            writer.writerow(np.append(p, t))
                    else:
                        for p in points:
                            writer.writerow(p)

        print("Sending msg to ventilator")
        self.to_ventilator.send_string("end")
        self.to_ventilator.recv()

    def __init__(self, my_dir, dir_ventilator):
        self.my_dir = my_dir
        self.dir_ventilator = dir_ventilator
        self.createSockets()


def createConsole():
    console = argparse.ArgumentParser()
    console.add_argument("my_dir", type=str)
    console.add_argument("dir_ventilator", type=str)
    return console.parse_args()


if __name__ == "__main__":
    args = createConsole()
    sink = Sink(args.my_dir, args.dir_ventilator)
    sink.listen()