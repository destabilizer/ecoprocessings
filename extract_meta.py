import exifread
from kthread import KThread
import pymongo
from datetime import datetime
import time
import os
import os.path

db_collection = None
thread_amount = None
time_penalty = None

def get_exif_from_image(image_filename):
    with open(image_filename, 'rb') as image_file:
        tags = exifread.process_file(image_file)
    for k in tags.keys():
        if type(tags[k]) == bytes:
            tags.pop(k)
        else:
            tags[k] = str(tags[k])
    tags['filename'] = image_filename
    return tags
    
def process_image_to_db(filename):
    t = get_exif_from_image(filename)
    db_collection.insert_one(t)
    print('processed', filename)

def process_exifs_to_db(*directories, threads=8, tp=3):
    global db_collection, thread_amount, time_penalty
    thread_amount = threads
    time_penalty = tp
    mc = pymongo.MongoClient()
    db = mc['exif']
    dt = datetime.now().strftime("%d.%m.%Y_%H.%M")
    db_collection = db[dt]
    for d in directories:
        print('processing directory', d)
        process_directory(d)

def process_directory(d):
    print('processing directory', d)
    images = os.listdir(d)
    thread_list = [('', None, 0)]*thread_amount
    while True:
        for ti in range(thread_amount):
            if len(images) == 0: break
            t = thread_list[ti]
            t_image, t_thread, t_time = t
            cur_time = time.time()
            if t_image and t_thread.isAlive():
                if (cur_time - t_time) < time_penalty: continue
                t_thread.terminate()
                print('killling thread for', t_image)
                images.append(t_image)
            cur_image = os.path.join(d, images[0])
            cur_thread = KThread(target = process_image_to_db, args=(cur_image))
            thread_list[ti] = (cur_image, cur_thread, cur_time)
            images.pop(0)
            cur_thread.start()
            
