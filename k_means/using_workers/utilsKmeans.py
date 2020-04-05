import matplotlib.pyplot as plt 
def show(clusters, centroids = None):
    colors = ["red", "green", "blue", "lime", "salmon", "skyblue"]
    n_colors = len(colors)
    for i, cluster in enumerate(clusters):
        if cluster.shape[0] != 0:
            color = i % n_colors
            plt.scatter(cluster[:, 0], cluster[:, 1], c = colors[color])

    if centroids is not None:
        for centroid in centroids:
            if centroid.shape[0] != 0:
                plt.scatter(centroid[0], centroid[1], c="black", marker = "D", linewidths=5) 
    plt.show()



