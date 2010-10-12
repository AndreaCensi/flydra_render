import numpy

import procgraph_flydra.optics_480x240 as optics
pixelmap = numpy.array(optics.pixelmap)    

from procgraph.components.basic import register_simple_block

def values2retina(values):
    
    n = len(values)
    valuesp = numpy.ndarray(shape=(n + 1,))
    
    valuesp[0:n] = values
    #valuesp[n] = numpy.NaN
    valuesp[n] = 0
    
    print pixelmap.max()
    
    return valuesp[pixelmap]


register_simple_block(values2retina)
