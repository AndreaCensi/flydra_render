import numpy
from reprep import Report
from reprep.graphics.posneg import posneg
from procgraph_flydra.values2retina import values2retina

def create_report_delayed(exp_id, delayed):
    
    delays = numpy.array(sorted(delayed.keys()))
    
    r = Report(exp_id)
    
    for delay in delays:
        data = delayed[delay]
        
        a = data['action_image_correlation']
        
        rr = r.node('delay%d' % delay)
        
        rr.data_rgb('action', posneg(values2retina(a)))
        
        f = rr.figure()
        f.sub('action')
                
    return r 
