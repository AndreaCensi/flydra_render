from procgraph_flydra.values2retina import add_reflines, values2retina
from reprep import scale, posneg

def add_scaled(report, id, x, **kwargs):
    n = report.data(id, x)
    
    n.data_rgb('retina',
            add_reflines(scale(values2retina(x), min_value=0, **kwargs)))
    
    #with n.data_pylab('plot') as pylab:
    #    pylab.plot(x, '.')
        
    return n
        
def add_posneg(report, id, x, **kwargs):
    n = report.data(id, x)
    
    n.data_rgb('retina',
            add_reflines(posneg(values2retina(x), **kwargs)))
    
    #with n.data_pylab('plot') as pylab:
    #    pylab.plot(x, '.')
        
    return n
