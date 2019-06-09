from pymongo import MongoClient
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

graph_name = str()
graph_axis_names = list()
X, Y = list(), list()
model_func = None
model_name = str()
axis = [0, 1, 0, 1]
r2 = None

def add_data(field_x, field_y, dbname, filter_func=lambda x, y: True):
    "Add data from database"
    global graph_name, graph_params
    graph_name = dbname
    graph_axis_names.extend((field_x, field_y))
    global X, Y
    mc = MongoClient()
    db = mc[dbname]
    col = db[db.list_collection_names()[0]]
    X, Y = list(), list()
    for d in col.find():
        x, y = d[field_x], d[field_y]
        if filter_func(x, y):
            X.append(x)
            Y.append(y)

def build_linear():    
    global model_func, model_name, r2
    model_name = 'linear'
    slope, intercept, r_value, p_value, std_err = stats.linregress(X,Y)
    coeff = (slope, intercept)
    model_func = lambda x: np.polyval(coeff, x)
    r2 = r_value**2
    return coeff

def build_quad():
    global model_func, model_name, r2
    model_name = 'quad'
    coeff = np.polyfit(X, Y, 2)
    model_func = lambda x: np.polyval(coeff, x)
    return coeff

def cut_length(x, y, length=-1):
    m = min(len(x), len(y))
    length = m if length == -1 else min(length, m)
    return (x[:length], y[:length])

def convert_shift(shift):
    if shift >= 0:
        return (0, shift)
    else:
        return (-shift, 0)

def align_data(x, y, shift=0, length=-1):
    cs = convert_shift(shift)
    return cut_length(x[cs[0]:], y[cs[1]:], length)

def draw_plot():
    xtest = np.arange(axis[0], axis[1], (axis[1]-axis[0])/100)
    ytest = model_func(xtest)
    plt.plot(X, Y, 'bo')
    plt.plot(xtest, ytest, 'r')
    plt.axis(axis)
    plt.xlabel(graph_axis_names[0])
    plt.ylabel(graph_axis_names[1])
    plt.text(0, 0, 'R^2='+str(r2))
    plt.savefig(graph_name+'_'+model_name+'.png')
    plt.clf()

