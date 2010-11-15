import numpy
from reprep import Report
from reprep.graphics.posneg import posneg
from procgraph_flydra.values2retina import values2retina, add_reflines

def create_report_delayed(exp_id, delayed, description):
    
    delays = numpy.array(sorted(delayed.keys()))
    
    r = Report(exp_id)
    r.text('description', description)
    
    f = r.figure(shape=(3,3))
    
    # max and sum of correlation for each delay
    corr_max = []
    corr_mean = []
    
    for delay in delays:
        data = delayed[delay]
        
        a = data['action_image_correlation']
        
        id = 'delay%d' % delay
        
        #rr = r.node('delay%d' % delay)
        r.data(id, a).data_rgb('retina', add_reflines(posneg(values2retina(a))))
        
        corr_mean.append(numpy.abs(a).mean()) 
        
        caption = 'delay: %d (max: %.3f, sum: %f)' % (delay, numpy.abs(a).max(),
                                                      numpy.abs(a).sum())
        f.sub(id, caption = caption)
    
    
    timestamp2ms = lambda x: x * (1.0/60) * 1000
    
    peak = numpy.argmax(corr_mean)
    peak_ms = timestamp2ms(delays[peak])
    with r.data_pylab('mean') as pylab:
        T = timestamp2ms(delays)  
        pylab.plot(T, corr_mean, 'o-')
        pylab.ylabel('mean correlation field')
        pylab.xlabel('delay (ms) ')
        
        a = pylab.axis()
        
        pylab.plot([0,0],[a[2], a[3]],'k-')
        
        y = a[2] + (a[3]-a[2])*0.1
        pylab.text(+5, y, 'causal', horizontalalignment='left')
        pylab.text(-5, y, 'non causal', horizontalalignment='right')
        
        pylab.plot([peak_ms, peak_ms],[a[2], max(corr_mean)   ],'b--')
        
        y = a[2] + (a[3]-a[2])*0.2
        pylab.text(peak_ms+10, y, '%d ms' % peak_ms, horizontalalignment='left' )
    
    f = r.figure('stats')
    f.sub('mean')
        
    a = delayed[int(delays[peak])]['action_image_correlation']
    r.data_rgb('best_delay', add_reflines(posneg(values2retina(a))))
    
    return r 
