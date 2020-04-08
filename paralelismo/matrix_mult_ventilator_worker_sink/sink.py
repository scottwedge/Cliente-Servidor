import zmq 
import numpy as np
import argparse
import time
class Sink:

    #Crea el socket donde le llega la informacion del 
    #ventilator, que son el numero de operaciones a recibir
    def createSockets(self):
        self.context = zmq.Context()

        self.from_ventilator = self.context.socket(zmq.PULL)
        self.from_ventilator.bind(f"tcp://{self.dir_sink}")

    
    #Pega todas las respuestas de los workers en una matriz
    def operate(self, type_operation, rows, cols):
        result_matrix =  np.zeros((rows, cols))
        opers = 0
        if type_operation == "row-matrix":
            opers = rows
        elif type_operation == "row-column":
            opers = rows*cols 


        print("\n\n\n\nTotal opers", opers)
        t_ini = time.time()
        for op in range(opers):
            #print("Oper", op)
            msg = self.from_ventilator.recv_json()
            result = np.asarray(msg["c"])
            pos = msg["position"]

            #Si la multiplicacion que hizo el worker fue de fila*columna, 
            #entonces la posicion es de una celda y estara en formato x,y
            #por lo que la arregla antes de agregarla a la matriz
            if type_operation == "row-column":
                f, c = pos.split(",")
                f = int(f)
                c = int(c)
                result_matrix[f, c] = result
            #Si no, sobreescribe toda una fila de la matriz resultante
            else:
                f = int(pos)
                result_matrix[f, :] = result
        print(f"\n\n\nTime with paralelism {time.time()-t_ini}")
        return result_matrix

    #Funcion donde le llegara el mensaje del ventilator, mandara a pegar
    #las partes de la matriz y mostrara el resultado
    def listen(self):
        msg = self.from_ventilator.recv_json()
        rows = msg["rows"]
        cols = msg["cols"]
        type_operation = msg["type"]
        result_matrix = self.operate(type_operation, rows, cols)
        print(result_matrix)
        
    def __init__(self, dir_sink):
        self.dir_sink = dir_sink
        self.createSockets()

if __name__ == "__main__":
    console = argparse.ArgumentParser()
    console.add_argument("dir_sink", type=str)
    dir_sink = console.parse_args().dir_sink

    sink = Sink(dir_sink)
    sink.listen()