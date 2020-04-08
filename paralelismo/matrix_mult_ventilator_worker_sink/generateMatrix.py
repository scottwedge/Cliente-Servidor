import random 
import argparse
import numpy as np
from os.path import join
import json

"""
Archivo que genera dos matrices con numeros aleatorios
segun dos shapes dados, los guardara en un archivo json 
"""

def createConsole():
    console = argparse.ArgumentParser()
    console.add_argument("shape_matrix_a", type=str)
    console.add_argument("shape_matrix_b", type=str)
    console.add_argument("name_file", type=str)
    return console.parse_args()

def extractShapes(shape_str_a, shape_str_b):
    r1, c1 = shape_str_a.split(',')
    r2, c2 = shape_str_b.split(',')
    r1, c1, r2, c2 = [int(i) for i in [r1, c1, r2, c2]]
    if c1 != r2:
        raise Exception("El numero de columnas de a debe ser igual al", 
                         "numero de filas de b")
    return ((r1, c1), (r2, c2))

def createRandomMatrix(shape_a, shape_b):
    a = np.random.randint(low = -10, high = 10, size = shape_a).tolist()
    b = np.random.randint(low = -10, high = 10, size = shape_b).tolist()
    return a, b

def save_json(a, b, name_file):
    to_save = {
        "M1": a, 
        "M2" : b
    }
    to_save = json.dumps(to_save)

    with open(join("arrays", name_file + ".json"), "w") as f:
        f.write(to_save)
    print("Saved")


if __name__ == "__main__":
    args = createConsole()
    shape_a, shape_b = extractShapes(args.shape_matrix_a, args.shape_matrix_b)
    a, b = createRandomMatrix(shape_a, shape_b)
    #print(a)
    #print(b)
    save_json(a, b, args.name_file)