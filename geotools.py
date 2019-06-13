import numpy as np
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return km

# def spherical_dist(pos1, pos2, r=3958.75):
#     print(len(pos1))
#     print(len(pos2))
#     pos1 = np.array(pos1)
#     pos2 = np.array(pos2)
#     nzeros = len(pos1)-len(pos2)
#     zeros = np.zeros((-nzeros if nzeros < 0 else nzeros, 2))
#     if nzeros >= 0:
#         pos2 = np.concatenate((pos2, zeros), axis=0)
#     else:
#         pos1 = np.concatenate((pos1, zeros), axis=0)
#     print(len(pos1))
#     print(len(pos2))
#     return _spherical_dist(pos1, pos2, r)

def spherical_dist_matrix(pos1, pos2):
    pos1 = np.array(pos1)
    pos2 = np.array(pos2)
    return spherical_dist(pos1[:, None], pos2)

def spherical_dist(pos1, pos2, r=3958.75):
    '''
    This is function that calculates spherical distance from Jaime answer
     https://stackoverflow.com/questions/19413259/efficient-way-to-calculate-distance-matrix-given-latitude-and-longitude-data-in
    '''
    pos1 = pos1 * np.pi / 180
    pos2 = pos2 * np.pi / 180
    cos_lat1 = np.cos(pos1[..., 0])
    cos_lat2 = np.cos(pos2[..., 0])
    cos_lat_d = np.cos(pos1[..., 0] - pos2[..., 0])
    cos_lon_d = np.cos(pos1[..., 1] - pos2[..., 1])
    return r * np.arccos(cos_lat_d - cos_lat1 * cos_lat2 * (1 - cos_lon_d))

def get_norm_coord(deg_repr):
    d, m, s = deg_repr[1:-1].split(', ')
    d = int(d)
    m = int(m)/60
    s = s.split('/')
    s = int(s[0])/(int(s[1])*3600)
    return d+m+s
