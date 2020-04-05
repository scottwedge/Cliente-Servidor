import zmq
import numpy as np
import time
"""
EL ventilator:
1.Recibira las dos matrices y le enviara el trabajo alos workers
2.Le dira al sink cuantos mensajes debe esperar que le lleguen de 
los workers 
"""


class Ventilator:
    #Crea los sockets hacia los workers y hacie el sink
    #ambos de tipo push porque es el ventilator el que 
    #agrega informacion
    def createSockets(self):
        self.context = zmq.Context()

        self.to_sink = self.context.socket(zmq.PUSH)
        self.to_sink.connect(f"tcp://{self.dir_sink}")
        
        self.to_workers = self.context.socket(zmq.PUSH)
        self.to_workers.bind(f"tcp://{self.dir_ventilator}")

    #Primer caso de multiplicacion, cuando se ,ultiplica una fila 
    #de a por la matriz entera de b, asi, cada worker estaria cal-
    #culando una fila de la matriz resultante
    def multRowMatrix(self):
        n_rows_a = np.shape(self.a)[0]
        #Envio el numero de operaciones que recibe el sink
        self.to_sink.send_json({
            "type" : "row-matrix", 
            "rows" : n_rows_a,
            "cols" : np.shape(self.b)[1]
        })

        #Envio el trabajo a los workers
        for r in range(n_rows_a):
            self.to_workers.send_json({
                "a" : np.ndarray.tolist(self.a[r, :]),
                "b" : np.ndarray.tolist(self.b), 
                "position" : str(r), 
            })

    #Segundo caso de multiplicacion, en este caso, cada worker
    #se le envia una fila de a y una columna de b, entonces, 
    #estarian calculando solo una celda de la matriz resultante
    def multRowColumn(self):
        rows = np.shape(self.a)[0]
        cols = np.shape(self.b)[1]

        self.to_sink.send_json({
            "rows" : rows, 
            "cols" : cols, 
            "type" : "row-column"
        })
        #Envio de informacion a los workers
        for r in range(rows):
            for c in range(cols):

                self.to_workers.send_json({
                    "a" : np.ndarray.tolist(self.a[r, :]),
                    "b" : np.ndarray.tolist(self.b[:, c]),
                    "position" : str(r) + "," + str(c)
                })

    def __init__(self, a, b, dir_ventilator, dir_sink):
        self.a = a
        self.b = b
        self.dir_ventilator = dir_ventilator
        self.dir_sink = dir_sink
        print("A\n", self.a)
        print("B\n", self.b)
        t_ini = time.time()
        print("Expected value in sink\n", self.a.dot(self.b))
        print(f"Total time without paralelism: {time.time() - t_ini}")
        self.createSockets()

