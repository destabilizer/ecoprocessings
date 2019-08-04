## EcoProcessing

This library contains some tools for post processings data, that had been collected with ecostation clients and ecostatus server.

#### Description of modules

+ geotools.py
This module contatins some functions for geodata calculations,
for example, matrix of distance for points given in long/lat
coordinates (that is done by function spherical_dist)

+ model.py
This module contains routines that needs for data analysis and building
simple module. Using it you can add data from database (or just directly,
specifing model.X and model.Y) and try linear or quadratic regression 
(with functions build_linear and build_quad). After all, you can draw the
plot using matplotlib, using the function draw_plot.
Используя этот модуль, я нашел корреляцию между двумя датчиками света и
использовал ее для вычислений в sensors.py

+ soundfit.py, sound.py
Эти модули нужны были для калибровки звука, но эксперименты провалились.

+ sensors.py
Contains routines for converting data from database to absolute SI values.

+ meta.py
Contains functions for extracting and writing exif metadata from images to mongo and from database to images

+ remap_exif_gps.py
This module contains tools for synchronising gps coordinates lines with different timestamps
and then correcting one to another.
Во время синхронизации наборов координат надо выбрать самый подходящий кластер, пока как правило я выбирал самый большой. Дальше для ремапинга координат надо использовать функцию process_img_meta_linear или ее threaded версию process_img_meta