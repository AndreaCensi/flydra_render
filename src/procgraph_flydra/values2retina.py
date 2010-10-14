import numpy

import procgraph_flydra.optics_480x240 as optics
from procgraph.components.images.copied_from_reprep import posneg, scale


pixelmap = numpy.array(optics.pixelmap)    

from procgraph.components.basic import register_simple_block

def values2retina(values, background=numpy.NaN):
    
    n = len(values)
    valuesp = numpy.ndarray(shape=(n + 1,))
    
    valuesp[0:n] = values
    valuesp[n] = background
    
    return valuesp[pixelmap]


register_simple_block(values2retina)


def plot_luminance(values):
    n = len(values)
    r = numpy.ndarray(shape=(n + 1), dtype='uint8')
    g = numpy.ndarray(shape=(n + 1), dtype='uint8')
    b = numpy.ndarray(shape=(n + 1), dtype='uint8')
    
    r[0:n] = values * 255
    g[0:n] = values * 255
    b[0:n] = values * 255

    # background color    
    r[n] = 128
    g[n] = 128 
    b[n] = 128
    
    rgb = numpy.ndarray(shape=(pixelmap.shape[0], pixelmap.shape[1], 3), dtype='uint8')
    rgb[:, :, 0] = r[pixelmap]
    rgb[:, :, 1] = g[pixelmap]
    rgb[:, :, 2] = b[pixelmap]
    
    return rgb

register_simple_block(plot_luminance)
    
    
def plot_nearness(values):
    distance = 1.0 / values
    im = values2retina(distance, background=numpy.NaN)
    return scale(im, min_color=[0, 0, 0], max_color=[0, 1, 0], nan_color=[0.5, 0.5, 0.5])

def plot_rv(values):
    vx = values[ :, 1]
    #vy = values[1, :]
    
    image = values2retina(vx, background=numpy.NaN)
    
    return posneg(image)


register_simple_block(plot_rv)

    
    
