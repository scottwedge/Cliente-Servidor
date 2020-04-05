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


def k_means(data, n_clusters):
    n_data = data.shape[0]
    n_features = data.shape[1]
    
    mins_max = calculateMinMaxFeatures(data, n_features)
    centroids = createCentroids(mins_max, n_clusters, n_features)

    y = np.zeros(n_data)
    changing = True
    while changing:
        y_new = calculateDistanceAndAssign(data, centroids)
        if np.array_equal(y, y_new):
           changing = False
        else:
            y = y_new
            clusters = divideData(data, y, n_clusters, n_data, n_features)
            # show(clusters, centroids = centroids)

            centroids = moveCentroid(clusters, centroids)
            # clear_output(wait = True)
            # time.sleep(0.5)
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


