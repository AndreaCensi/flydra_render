import numpy
from reprep import Report
from reprep.graphics.posneg import posneg
from procgraph_flydra.values2retina import values2retina

def create_report_delayed(exp_id, delayed):
    
    delays = numpy.array(sorted(delayed.keys()))
    
    r = Report(exp_id)
    f = r.figure(shape=(3,3))
    
    # max and sum of correlation for each delay
    corr_max = []
    corr_mean = []
    
    for delay in delays:
        data = delayed[delay]
        
        a = data['action_image_correlation']
        
        id = 'delay%d' % delay
        
        #rr = r.node('delay%d' % delay)
        
        r.data_rgb(id, posneg(values2retina(a)))
        
        corr_mean.append(numpy.abs(a).mean()) 
        
        caption = 'delay: %d (max: %.3f, sum: %f)' % (delay, numpy.abs(a).max(),
                                                      numpy.abs(a).sum())
        f.sub(id, caption = caption)
        
    with r.data_pylab('mean') as pylab:
        T = delays * (1.0/60) * 1000
        pylab.plot(T, corr_mean)
        pylab.ylabel('mean correlation field')
        pylab.xlabel('delay (ms) ')
        
    
    f = r.figure('stats')
    f.sub('mean')
        
    return r 
