import numpy as np

block_size = -1
blocks = []

def calc_block_size(interval, samplerate):
    return (interval * samplerate)//1000

def check_data_position(block_number, data_size, samplerate, interval, offset, end):
    ms_time = block_number * interval + offset
    if end != -1:
        ms_time_block_end = (block_number+1) * interval + offset
        if ms_time_block_end > end: return -1
    data_pos = (ms_time * samplerate) // 1000
    if data_pos + block_size < data_size:
        return data_pos
    else:
        return -1

def compose_blocks(data, samplerate, interval, offset=0, end=-1):
    global blocks, block_size
    data_shape = data.shape
    data_size = data_shape[0]
    block_size = calc_block_size(interval, samplerate)
    block_shape = (block_size,) + data_shape[1:]
    current_block = None
    block_number = -1
    inner_block_counter = block_size
    dp = lambda n: check_data_position(n, data_size, samplerate, interval, offset, end)
    while True:
        if block_number >= 0: blocks.append(current_block)
        block_number += 1
        p = dp(block_number)
        if p == -1: break
        current_block = np.zeros(block_shape)
        for i in range(block_size):
            current_block[i] = data[p+i]

def clear_blocks():
    global blocks, block_size
    blocks = list()

def measure_db(calibration_offset = 0.):
    db_level = list()
    for b in blocks:
        db = 10*np.log10(np.mean(b**2))
        db_level.append(calibration_offset + db)
    return db_level

