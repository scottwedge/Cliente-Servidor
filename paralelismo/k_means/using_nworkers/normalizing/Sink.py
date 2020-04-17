import numpy as np 
import pandas as pd 
import zmq
import argparse
import os 
import csv

class Sink:

    def createSockets(self):
        self.context = zmq.Context()
        self.reciever = self.context.socket(zmq.PULL)
        self.reciever.bind(f"tcp://{self.my_dir}")
        
        self.to_ventilator = self.context.socket(zmq.REQ)
        self.to_ventilator.connect(f"tcp://{self.dir_ventilator}")
        


    def calculateMedia(self):
        average_points = None
        for i in range(self.opers):
            msg = self.reciever.recv_json()
            print("Recieved msg  media from worker")

            if average_points is None:
                average_points = np.asarray(msg["sum_points"])
            else:
                average_points +=  np.asarray(msg["sum_points"])

        average_points = average_points / self.n_data
        print("Sending media to ventilator")
        self.to_ventilator.send_json({
            "average_points" : np.ndarray.tolist(average_points)
        })
        self.to_ventilator.recv()

    def calculateDesvesta(self):
        desvesta = None

        for i in range(self.opers):
            msg = self.reciever.recv_json()
            print("Recieved msg desvesta from worker")
            
            if desvesta is None:
                desvesta = np.asarray(msg["sum_points"])
            else:
                desvesta +=  np.asarray(msg["sum_points"])

        desvesta = np.sqrt(desvesta / self.n_data)
        print("Sending desvesta to ventilator")
        self.to_ventilator.send_json({
            "desvesta" : np.ndarray.tolist(desvesta)
        })
        self.to_ventilator.recv()

    def listen(self):

        print("ready")
        initial_data = self.reciever.recv_json()
        self.n_data = initial_data["n_data"]
        self.opers =  initial_data["opers"]
        print("Initial data recieved")

        self.calculateMedia()
        self.calculateDesvesta()

        print("Sending end to ventilator")
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