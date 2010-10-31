import numpy 
import scipy.stats

from reprep import Report
from mamarama_analysis.first_order_data import get_all_data_for_signal


def compute_general_statistics(id, db, samples, interval_function, 
                               signal, signal_component):
    r = Report(id)
    
    x = get_all_data_for_signal(db, samples, interval_function, 
                                signal, signal_component)
    
    limit = 0.3
    
    perc = [0.001, limit, 1, 10, 25, 50, 75, 90, 99, 100-limit, 100-0.001]
    xp = map(lambda p: "%.3f" % scipy.stats.scoreatpercentile(x, p), perc)
    
    lower = scipy.stats.scoreatpercentile(x, limit)
    upper = scipy.stats.scoreatpercentile(x, 100-limit)
    
    f = r.figure()
    
    with r.data_pylab('histogram') as pylab:
        bins =numpy. linspace(lower, upper, 100)
        pylab.hist(x,bins=bins)
        
    f.sub('histogram')

    
    labels = map(lambda p: "%.3f%%" % p, perc)
    
    
    r.table("percentiles", data=[xp], cols=labels, caption="Percentiles")
    
    r.table("stats", data=[[x.mean(), x.std()]], cols=['mean', 'std.dev.'], 
            caption="Other statistics")

    print "Computing correlation..."
    corr, lags = xcorr(x, maxlag=20)
    print "...done."

    with r.data_pylab('cross_correlation') as pylab:
        delta = (1.0/60) * lags
        pylab.plot(delta, corr, 'o-')
        
        pylab.axis([min(delta), max(delta), -0.7, 1.1])
    
    
    f = r.figure()
    f.sub('cross_correlation')

     
    return r



def xcorr(a, b=None, maxlag=None):
    ''' Returns a tuple  (values, lags):
    
            plot(lags, values)
    '''
    
    if b is None:
        b = a
    a = numpy.array(a)
    b = numpy.array(b)
    
    if maxlag is None:
        maxlag = len(a) / 2
        
    # normalize a, b
    a = a - a.mean()
    b = b - b.mean()
    
    na = numpy.linalg.norm(a)
    nb = numpy.linalg.norm(b)
    if na > 0:
        a = a / na
    if nb > 0:
        b = b / nb
        
    lags = range(-maxlag, maxlag + 1)
    results = numpy.zeros(shape=(len(lags),))
    for i, lag in enumerate(lags):
        if lag < 0:
            lag = -lag
            ta, tb = b, a
        else:
            ta, tb = a, b
        part_of_a = ta[lag:len(tb)]
        part_of_b = tb[0:len(part_of_a)]
        assert len(part_of_a) == len(part_of_b)
        results[i] = (part_of_a * part_of_b).sum()

    return results, numpy.array(lags)

