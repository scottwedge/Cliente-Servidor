from ventilator import Ventilator
import pandas as pd 
from os.path import join 
import argparse
if __name__ == "__main__":
    console = argparse.ArgumentParser()
    console.add_argument("name_file", type = str)
    console.add_argument("n_clusters", type = int)
    args = console.parse_args()
    name_file = args.name_file
    n_clusters = args.n_clusters

    ventilator = Ventilator(name_file, True, 
                            "127.0.0.1:5555", 
                            "127.0.0.1:5556", 
                            "127.0.0.1:5557", 
                            n_clusters, "euclidean")
    tags_true = pd.read_csv(join("datasets", name_file), usecols=["tag"]).values
    ventilator.kmeans()
    
    tags_pred = ventilator.y
    clusters = []
    for i in range(n_clusters):
        clusters.append([0]*n_clusters)
    print(clusters)
    for i, tag in enumerate(tags_pred):
        clusters[tag][int(tags_true[i][0])] += 1

    for i, c in enumerate(clusters):
        print("\tCLUSTER", str(i+1))
        print([f"Tag {j+1}: {c[j]}" for j in range(len(c))])




    