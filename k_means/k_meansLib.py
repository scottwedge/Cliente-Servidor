from scipy.spatial import distance
from IPython.display import clear_output
import time
import numpy as np 
from sklearn.datasets import make_blobs
import argparse 
from utilsKmeans import *


def divideData(x, y, n_clusters, n_data, n_features):
    clusters = []
    for cluster in range(n_clusters):
        clusters.append(np.array([x[i, :] for i in range(n_data) if y[i] == cluster]))
    return clusters

def calculateDistanceAndAssign(data, centroids):
    y = np.zeros(data.shape[0])
    for i, d in enumerate(data):
        y[i] = np.argmin(np.array([distance.euclidean(d, centroid) for centroid in centroids]))
    return y

def moveCentroid(points_groups, old_centroids):
    centroids = []
    for i, group in enumerate(points_groups):
        if group.shape[0] != 0:
            centroids.append(np.average(group, axis = 0))
        else:
            centroids.append(old_centroids[i])
    return centroids


def calculateMinMaxFeatures(data, n_features):
    mins_max = []
    for i in range(n_features):
        min_f = np.min(data[:, 0])
        max_f = np.max(data[:, 0])
        mins_max.append((min_f, max_f))
    return mins_max

def createCentroids(mins_max, n_clusters, n_features):
    centroids = np.zeros((n_clusters, n_features))
    for i in range(n_clusters):
        for j, min_max in enumerate(mins_max):
            centroids[i][j] = np.random.uniform(low = min_max[0], high = min_max[1])
    return centroids

def isEmptyCluster(clusters):
    empty = False
    i = 0
    while not empty and i < len(clusters):
        if clusters[i].shape[0] == 0:
            empty = True
        i += 1
    return empty

def k_means(data, n_clusters):
    n_data = data.shape[0]
    n_features = data.shape[1]

    #Creo los centroides de manera aleatoria en el rango 
    #de cada dimension de los puntos
    mins_max = calculateMinMaxFeatures(data, n_features)
    centroids = createCentroids(mins_max, n_clusters, n_features)

    y = np.zeros(n_data)
    changing = True
    while changing:
        #Calculo la distancia de cada punto a todos los clusters 
        #y lo asigno a un cluster
        y_new = calculateDistanceAndAssign(data, centroids)
        #Si ningun punto ha cambiado de cluster paro de iterar
        if np.array_equal(y, y_new):
           changing = False
        else:
            y = y_new
            #Divido los puntos por clusters, segun el y calculado antes
            clusters = divideData(data, y, n_clusters, n_data, n_features)
            #Volvemos a incializar los clusters hasta que todos 
            # #tengan al menos un elemento
            while isEmptyCluster(clusters):
                print("Empty cluster!")
                centroids = createCentroids(mins_max, n_clusters, n_features)
                clusters = divideData(data, y, n_clusters, n_data, n_features)

        #Muevo los centroides a la media de los puntos que le pertenecen
        centroids = moveCentroid(clusters, centroids)

    print("Acabe")
    if n_features == 2:
        show(clusters, centroids=centroids)
    return clusters 

def createConsole():
    console = argparse.ArgumentParser()
    console.add_argument("n_clusters", type=int)
    console.add_argument("n_features", type=int)
    args = console.parse_args()
    return args.n_clusters, args.n_features

if __name__ == "__main__":
    n_clusters, n_features = createConsole()
    samples = 300
    x, y = make_blobs(n_samples = samples, n_features=n_features, centers=n_clusters)

    #Mostrando el dataset
    clusters = divideData(x, y, n_clusters, samples, n_features)
    if n_features == 2:
        show(clusters)


    clusters = k_means(x, n_clusters)
    for i, cluster in enumerate(clusters):
        print(f"\tCLUSTER {i+1}")
        print(cluster)


