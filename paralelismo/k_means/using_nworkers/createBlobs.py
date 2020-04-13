"""
Con este programa se pueden crar datasets con la funcion 'make_blobs' 
de sklearn y guardarlos en un CSV, asi, se puede tener un dataset con 
cualquier numero de features y clusters 
"""
from sklearn.datasets import make_blobs
import pandas as pd
import argparse 
import random
from os.path import join
import csv 
import numpy as np 

def createConsole():
    console = argparse.ArgumentParser(description="Creando datasets")
    console.add_argument("name", type=str)
    console.add_argument("clusters", type=int)
    console.add_argument("features", type=int)
    console.add_argument("samples", type=int)
    return console.parse_args()

def createDataset(name, clusters, features, samples):
    x, y = make_blobs(n_samples=samples, n_features=features, 
                        centers=clusters, random_state=random.randint(0, 100))


    with open(join("datasets", name), 'w') as f:
        writer = csv.writer(f)
        
        col_names = [f"feature_{i}" for i in range(features)]
        col_names.append("tag")
        writer.writerow(col_names)

        for i in range(samples):
            writer.writerow(np.append(x[i], y[i]))

if __name__ == "__main__":
    args = createConsole()
    createDataset(args.name, args.clusters, args.features, args.samples)
