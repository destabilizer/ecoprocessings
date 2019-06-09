from pymongo import MongoClient
import soundfile as sf
import sound
import model

micdata = None
sounddata = None
samplerate = None

def add_data(micdata_db, micdata_col, field_name, sound_filename):
    global micdata, sounddata, samplerate
    sounddata, samplerate = sf.read(sound_filename)
    micdata = list()
    mc = MongoClient()
    col = mc[micdata_db][micdata_col]
    for d in col.find():
        micdata.append(d[field_name])

def prepare_db_level(interval, offset):
    '''
    In this function we suppose that offset < interval
    '''
    sound.compose_blocks(sounddata, samplerate, interval, offset)
    return sound.measure_db()

def calculate_long_offset(interval, offset):
    per_offset = offset % interval
    shift = offset // interval
    return shift, per_offset

def prepare_sound_data_for_analysis(interval, offset):
    shift, per_offset = calculate_long_offset(interval, offset)
    db_level = prepare_db_level(interval, per_offset)
    model.X, model.Y = model.align_data(micdata, db_level, shift)
    model.build_linear()
    model.graph_name = 'sound'
    model.axis = [0, 1, min(db_level), max(db_level)]
    model.graph_axis_names = ['sound sensor', 'dB']
    model.draw_plot()

def find_best_offset(interval, left_range=-5, right_range=5, step_precision=10, cutlen = 100):
    istep = interval//step_precision
    fits = list()
    for i in range(0, interval, istep):
        db_level = prepare_db_level(interval, i)
        for s in range(left_range, right_range):
            offset = s*interval + i
            f = check_fit(*model.align_data(micdata, db_level, s, cutlen))
            fits.append((f, offset))
    return fits

def check_fit(sensordata, dblevel):
    model.X = sensordata
    model.Y = dblevel
    model.build_linear()
    return model.r2

