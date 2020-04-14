from ventilator import Ventilator
import pandas as pd 
from os.path import join 

if __name__ == "__main__":
    ventilator = Ventilator("iris.csv", True, 
                            "127.0.0.1:5555", 
                            "127.0.0.1:5556", 
                            "127.0.0.1:5557", 
                            3)
    tags_true = pd.read_csv(join("datasets", "iris.csv"), usecols=["variety"]).values
    ventilator.kmeans()
    
    tags_pred = ventilator.y
    clusters = []
    for i in range(3):
        clusters.append([0, 0, 0])
    print(clusters)
    for i, tag in enumerate(tags_pred):
2        if tags_true[i][0] == "Setosa":
            clusters[tag][0] += 1
        elif tags_true[i][0] == "Versicolor":
            clusters[tag][1] += 1
        elif tags_true[i][0] == "Virginica":
            clusters[tag][2] += 1
    
    for i, c in enumerate(clusters):
        print("\tCLUSTER", str(i+1))
        print("Setosa: ", c[0])
        print("Versicolor: ", c[1])
        print("Virginica: ", c[2])




    