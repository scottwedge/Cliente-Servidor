import numpy as np
import argparse
import json
from ventilator import Ventilator
from os.path import join

def createConsole():
    console = argparse.ArgumentParser()
    console.add_argument("dir_ventilator", type = str)
    console.add_argument("dir_sink", type = str)
    console.add_argument("file_name", type = str)
    console.add_argument("type_of_divide", type=str)
    return console.parse_args()

def adapterNumpy(file_name):
    with open(join("arrays", file_name), "r") as f:
        data = json.loads(f.read())
    a = data["M1"]
    b = data["M2"]

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return a, b

if __name__ == "__main__":
    args = createConsole()
    a, b = adapterNumpy(args.file_name)
    ventilator = Ventilator(a, b, args.dir_ventilator, args.dir_sink)
    input("Press enter when the workers are ready")
    if args.type_of_divide == "row-matrix":
        ventilator.multRowMatrix()
    elif args.type_of_divide == "row-col":
        ventilator.multRowColumn()
    else:
        print("No es un tipo de division de la multiplicacion valida")