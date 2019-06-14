import os.path
from datetime import datetime
import random

import geotools
import numpy as np

import data_threading

img_collection = None
data_collections = []
data_d = []
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
    for dc in data_collections:
        for d in dc.find():
            data_d.append(d)

def load_sync_checkpoint():
    with open('#sync_ckpt#') as ckpt:
        L = ckpt.readlines()
    global timediff, timediff_min, timediff_max
    timediff, timediff_min, timediff_max = map(float, L[:3])

def _take_img():
    r = random.randrange(SYNC_DATA_PROB[0])
    return r < SYNC_DATA_PROB[1]

def get_datetime_from_image_filename(fn):
    fn = fn.split('/')[-1].split('\\')[-1]
    aftimg = fn.lower().split('img')[-1].strip('.jpg')
    ts = '_'.join(aftimg.split('_')[1:3])
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
    for d in data_d:
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

def find_best_data_fit_for_image(img_dt, time_epsilon=2):
    fit = []
    fit_counter = 0
    tdd = []
    for dc in data_collections:
        for d in data_d:
            dt = get_datetime_from_data_ts(d['gps_timest'])
            time_delta = (img_dt-dt).total_seconds()
            #if time_delta_diff < time_epsilon:
            #    good_fit.append((time_delta_diff, d))
            time_delta_diff = time_delta - timediff
            if abs(time_delta_diff) < time_epsilon:
                print('fast remaping')
                return time_delta_diff, d, dc.name
            elif timediff_min < time_delta < timediff_max:
                fit.append((d, dc.name))
                tdd.append((time_delta_diff, fit_counter))
                fit_counter += 1
            else:
                pass
    print('fit size', len(fit))
    if fit:
        _, i = min(map(lambda t: (abs(t[0]), t[1]), tdd))
        print('best timediff', tdd[i])
        return tdd[i], fit[i][0], fit[i][1]
    else:
        return -1

def process_data_element(d):
    print('started processing new img')
    dt = get_datetime_from_image_filename(d['filename'])
    bd = find_best_data_fit_for_image(dt)
    d['data'] = bd

def update_coordinates(d):
    if d['data'] == -1: return
    _id = d['_id']
    new_coord = {'X':d['data'][1]['X'], 'Y':d['data'][1]['Y']}
    print('new coordinates', new_coord)
    upd = new_coord
    upd['timediff'] = d['data'][0]
    upd['db'] = d['data'][2]
    img_collection.update({'_id': _id}, {'$set': upd})

def process_img_meta(skip_remapped=True, threads=4, timeout=20):
    tdm = data_threading.ThreadedDataManager(thread_amount=threads)
    tdm.setDataProcess(process_data_element)
    tdm.setTimeout(timeout)
    tdm.setOnSuccess(update_coordinates)
    for img in img_collection.find():
        if skip_remapped:
            if 'X' in img.keys() and 'Y' in img.keys():
                print('skip img')
                continue
        d = dict()
        d['_id'], d['filename'] = img['_id'], img['filename']
        tdm.append(d)

    print('all data is loaded')
    tdm.start()

def process_img_meta_linear(skip_remapped=True):
    for img in img_collection.find():
        if skip_remapped:
            if 'X' in img.keys() and 'Y' in img.keys():
                print('skip img')
                continue
        d = dict()
        d['_id'], d['filename'] = img['_id'], img['filename']
        process_data_element(d)
        update_coordinates(d)
