import zmq
import numpy as np 
import argparse


def isNumber(n):
    return isinstance(n, int) or isinstance(n, float)

class Worker:

    def listen(self): 
        #Ciclo en el que recibe los dos arrays y los multiplica
        while True:
            msg = self.from_ventilator.recv_json()
            a = np.asarray(msg["a"])
            b = np.asarray(msg["b"])
  
            print(np.shape(a), np.shape(b))
            #print(f"Operating {a} * \n{b}")
            # if np.shape(a)[1] != np.shape(b)[0]:
            #     b = b.T
            c = a.dot(b)
            #print("C:")
            #print(c)

            #Si es un numero, se le puede enviar c al sink sin 
            #necesidad de hacerle nada, pero si no lo es, se 
            #pasa el numpy array a una lista para que no moleste el json
            if not isNumber(c):
                c = np.ndarray.tolist(c)

            self.to_sink.send_json({
                "c" : c,
                "position" : msg["position"],
            })

    
    #Crea los sockets del ventilator y hacia el sink, 
    #como del ventilator recibe la informacion es de tipo
    #pull, pero al sink le envia informacion entonces es 
    #push
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