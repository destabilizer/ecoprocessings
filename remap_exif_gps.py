import os.path
from datetime import datetime
import random

import geotools
import numpy as np

img_collection = None
data_collections = []
timediff = None
timediff_min = None
timediff_max = None

cluster_info_str = 'cluster: {0} \t| amount: {1} \t| mean: {2} \t| min: {3} \t| max: {4} \t| median: {5}'

def add_data(data_db_name, data_col_names, img_db_name, img_col_name):
    from pymongo import MongoClient
    mc = MongoClient()
    global img_collection, data_collections
    img_collection = mc[img_db_name][img_col_name]
    data_collections = [mc[data_db_name][cn] for cn in data_col_names]

def _take_img():
    r = random.randrange(SYNC_DATA_PROB[0])
    return r < SYNC_DATA_PROB[1]

def get_datetime_from_image_filename(fn):
    fn = fn.split('/')[-1].split('\\')[-1]
    ts = '_'.join(fn.split('_')[1:3])
    dt = datetime.strptime(ts, '%Y%m%d_%H%M%S')
    return dt

def get_datetime_from_data_ts(ts):
    dt = datetime.strptime(ts, '%Y/%m/%d %H:%M:%S.%f')
    return dt

def cluster_info(cluster):
    amount = len(cluster)
    mean = sum(cluster)/amount
    minel = cluster[0]
    maxel = cluster[-1]
    median = cluster[amount//2]
    return (amount, mean, minel, maxel, median)

def sync_data(take_img_rand_func=lambda: random.randrange(100)<10, epsilon=0.003):
    choosed_images_gps = []
    choosed_images_dt = []
    for img in img_collection.find():
        if take_img_rand_func():
            try:
                lat = img['GPS GPSLatitude']
                lng = img['GPS GPSLongitude']
            except KeyError:
                continue
            gps = geotools.get_norm_coord(lat),\
                  geotools.get_norm_coord(lng)
            print('img gps', gps)
            dt = get_datetime_from_image_filename(img['filename'])
            choosed_images_gps.append(gps)
            choosed_images_dt.append(dt)
    data_gps = []
    data_dt = []
    for col in data_collections:
        for d in col.find():
            gps = d['latitude'], d['longitude']
            print('data gps', gps)
            dt = get_datetime_from_data_ts(d['gps_timest'])
            data_gps.append(gps)
            data_dt.append(dt)
    images_amount = len(choosed_images_gps)
    data_amount = len(data_gps)
    dist_matrix = geotools.spherical_dist_matrix(choosed_images_gps, data_gps)
    print(dist_matrix)
    print(dist_matrix.shape)
    time_diffs = list()
    for i in range(images_amount):
        dist = dist_matrix[i]
        for d in range(data_amount):
            if dist[d] < epsilon:
                print('img', i, 'and data', d, 'have near coordinates')
                td = choosed_images_dt[i]-data_dt[d]
                time_diffs.append(td.total_seconds())
                print('time delta between them is', td)
    time_diffs.sort()
    cluster_gap = int(input('enter preferable cluster gap: '))
    clusters = []
    p = time_diffs[0] - 2*cluster_gap
    for td in time_diffs:
        if td-p > cluster_gap:
            clusters.append([td])
        else:
            clusters[-1].append(td)
        p = td
    for c in range(len(clusters)):
        ci = cluster_info(clusters[c])
        print(cluster_info_str.format(c, *map(round, ci)))
    c = int(input('choose cluster: '))
    global timediff, timediff_min, timediff_max
    a, m, timediff_min, timediff_max, timediff = cluster_info(clusters[c])

def find_best_data_fit_for_image(img_dt, time_epsilon=3):
    fit = []
    for dc in data_collections:
        for d in dc.find():
            dt = get_datetime_from_data_ts(d['gps_timest'])
            time_delta = (img_dt-dt).total_seconds()
            #if time_delta_diff < time_epsilon:
            #    good_fit.append((time_delta_diff, d))
            time_delta_diff = abs(time_delta - timediff)
            if time_delta_diff < time_epsilon:
                print('fast remaping')
                return d
            elif timediff_min < time_delta < timediff_max:
                fit.append((time_delta_diff, d))
            else:
                pass
    print('fit', len(fit))
    if len(fit):
        fit.sort()
        print('timediff', fit[0][1])
        return fit[0][1]
    else:
        return -1

def process_img_meta():
    for img in img_collection.find():
        dt = get_datetime_from_image_filename(img['filename'])
        d = find_best_data_fit_for_image(dt)
        if d == -1: continue
        new_coord = {'X':d['X'], 'Y':d['Y']}
        print('new coordinates', new_coord)
        img_collection.update({'_id': img['_id']}, {'$set': new_coord})
