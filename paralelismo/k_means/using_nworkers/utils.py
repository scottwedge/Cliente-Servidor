import numpy as np 
"""
La similaridad oscila entre -1 y 1, por lo que no la podemos usar 
como medida de distancia porque viola la propiedad de positividad, 
el angulo oscila entre 0 y pi rad, donde pi rad es totalmente 
diferente y 0 son iguales, por lo que si se puede usar como medida
"""
def cosineSimilarity(p1, p2):
    p1 = np.asarray(p1)
    p2 = np.asarray(p2)
    if p1.shape[0] != p2.shape[0]:
        p2 = p2.T
    #Retorna el angulo (0-180 en rad) entre dos vectores 
    ab = p1.dot(p2)
    norm_a = np.linalg.norm(p1)
    norm_b = np.linalg.norm(p2)
    angle = np.arccos(ab/(norm_a*norm_b))
    return angle 


def cosineSimilarityForSparse(v1, v2)
    ab = v1.dot(v2.T).toarray()[0][0]
    norm_a = np.sqrt(np.sum(v1.power(2)))
    norm_b = np.sqrt(np.sum(v2.power(2)))
    angle = np.arccos(ab/(norm_a*norm_b))
    return angle