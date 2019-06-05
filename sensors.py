AMPERKA_GROVE_CORRELATION = [ 0.63738431, -1.42841419,  0.99381443]

import numpy

def amperka_light(dataval):
    if not (0 < dataval < 1): return
    old_light_value = dataval * 102.4
    sensorADC = int(round(old_light_value * 32))
    sensorADC = sensorADC >> 5
    sensorRatio = 1024 / sensorADC - 1
    sensorResistanse = 10000 / sensorRatio
    light_value = 32017200 / sensorResistanse ** 1.5832
    light_value = round(light_value, 2)
    return light_value

def grove_light(dataval):
    t = numpy.polyval(AMPERKA_GROVE_CORRELATION, dataval)
    #print(dataval, '->', t)
    return amperka_light(t)

def process_datatype(name, suffix, func, datadict):
    processed = func(datadict[name])
    return (name+'_'+suffix, processed)

def process_data(dbname):
    from pymongo import MongoClient
    mc = MongoClient()
    db = mc[dbname]
    for cn in db.list_collection_names():
        col =  db[cn]
        for du in col.find():
            new_values = list()
            new_values.append(process_datatype('light_at_top', 'lux', amperka_light, du))
            new_values.append(process_datatype('light', 'lux', grove_light, du))
            col.update_one({'_id': du['_id']}, {'$set': dict(new_values)})
            
