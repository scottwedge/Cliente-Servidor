import zmq 
import numpy as np 
import pandas as pd
import os 
import argparse

class Worker:


    datasets_path = os.path.join("/".join(os.getcwd().split("/")[:-1]), "datasets")


    def createSockets(self):
        self.context = zmq.Context()
        
        self.from_ventilator = self.context.socket(zmq.PULL)
        self.from_ventilator.connect(f"tcp://{self.dir_ventilator}")

        self.to_sink = self.context.socket(zmq.PUSH)
        self.to_sink.connect(f"tcp://{self.dir_sink}")

 

    def listen(self):
        print("ready")
        while True:
            msg = self.from_ventilator.recv_json()
            action = msg["action"]
            if action == "media":
                points = np.asarray(msg["points"])
                sum_points = np.ndarray.tolist(np.sum(points, axis = 0))
                n_elements = points.shape[0]
                print("Sending sum to sink")
                self.to_sink.send_json({
                    "action" : "media",
                    "sum_points" : sum_points, 
                    "n_elements" : n_elements
                })
            elif action == "desvesta":
                points = np.asarray(msg["points"])
                media = np.asarray(msg["media"])
                sum_points = np.sum((points-media)**2, axis = 0)
                sum_points = np.ndarray.tolist(sum_points)
                print("Sending sum desvesta to sink")
                self.to_sink.send_json({
                    "action" : "desvesta",
                    "sum_points" : sum_points, 
                })
            elif action == "normalize":
                has_tags = msg["has_tags"]
                media = np.asarray(msg["media"])
                desvesta = np.asarray(msg["desvesta"])
                if not has_tags:
                    points = np.asarray(msg["points"])
                    
                    print("Sending sum desvesta to sink")
                else:
                    points_tags = np.asarray(msg["points"])
                    points = points_tags[:, :-1]
                    tags = np.ndarray.tolist(points_tags[:, -1])
                
                points = points.astype(np.float)
                media = media.astype(np.float)
                desvesta = desvesta.astype(np.float)
                points = (points - media)/desvesta
                points = np.ndarray.tolist(points)

                response = {
                    "action" : "normalize",
                    "points" : points, 
                    "has_tags" : has_tags
                }
                if has_tags:
                    response["tags"] = tags

                print("Sending sum desvesta to sink")
                self.to_sink.send_json(response)

            elif action == "end":
                print("Sending end to sink")
                self.to_sink.send_json({
                    "action" : "end",
                })


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