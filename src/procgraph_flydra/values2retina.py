import numpy

from procgraph import simple_block

# XXX: to procgraph_images
from procgraph_images import posneg, scale, blend


# TODO: make this configurable

# We try to hide this from pydev
optics1 = __import__('procgraph_flydra.optics_640x240', fromlist=['dummy'])
pixelmap = optics1.pixelmap
optics2 = __import__('procgraph_flydra.optics_reflines_640x240', fromlist=['dummy'])
reflines = optics2.reflines

@simple_block
def values2retina(values, background=numpy.NaN):    
    n = len(values)
    valuesp = numpy.ndarray(shape=(n + 1,))
    
    valuesp[0:n] = values
    valuesp[n] = background
    
    return valuesp[pixelmap]


def add_reflines(rgb):
    return blend(rgb, reflines)




def plot_luminance(values):
    values = numpy.array(values)
    
    n = len(values)
    
    if n != 1398:
        raise Exception('Expected 1398 values, not %d.' % n)
    

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

register_simple_block(plot_nearness)


def plot_contrast(values):
    #print 'contrast', min(values), max(values)
    # im = values2retina(values, background=numpy.NaN)
    #print values[0:100].tolist()
    im = values2retina(values, background=numpy.NaN)
    return scale(im, min_color=[0, 0, 0], max_color=[0, 1, 1], nan_color=[0.5, 0.5, 0.5])

register_simple_block(plot_contrast)


def plot_rv(values):
    vx = values[ :, 1]
    #vy = values[1, :]
    
    image = values2retina(vx, background=numpy.NaN)
    
    return posneg(image)

register_simple_block(plot_rv)

