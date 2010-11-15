import numpy
import os

from compmake import set_namespace, compmake_console, comp, progress, comp_prefix
from optparse import OptionParser
from flydra_db  import FlydraDB

from mamarama_analysis.first_order_commands import xcorr
from reprep import Report


def main():
    set_namespace('env_stats')
    
    parser = OptionParser()

    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

    (options, args) = parser.parse_args() #@UnusedVariable


    db = FlydraDB(options.db, False)
    outdir = os.path.join(options.db, 'out/environment_stats')

    images = ["luminance", "contrast", "luminance_w", "contrast_w",
              "hluminance_w", "hcontrast_w"]
              
    for image in images:
        samples = [x for x in db.list_samples() 
                      if db.get_attr(x, 'stimulus', None) != 'nopost' and
                      db.has_table(x, image)]
        
        if not samples:
            print "No samples for %s" % samples
            continue
            
        comp_prefix(image)        
        data = comp(compute_environment_autocorrelation, options.db, samples, image)
        
        comp(create_report, data, image, outdir)
    

    db.close()
    
    compmake_console()
    
def create_report(data, image, outdir):
    r = Report('%s_stats' % image)
    
    xcorr = data['results']
    lags = data['lags']
    T = lags * (1.0/60) * 1000
    
    mean_xcorr = numpy.mean(xcorr,axis=0)
    min_xcorr = numpy.min(xcorr,axis=0)
    max_xcorr = numpy.max(xcorr,axis=0)
    
    with r.data_pylab('some') as pylab:
        
        for i in range(0,1000,50):
            pylab.plot(T, xcorr[i,:], 'x-', label='%d' % i)
    
        pylab.axis([T[0],T[-1],-0.5,1])
        pylab.xlabel('delay (ms)')
        pylab.ylabel('autocorrelation')
        pylab.legend()
    
    with r.data_pylab('mean_xcorr') as pylab:
        pylab.plot(T, mean_xcorr, 'x-')
        
        pylab.plot([T[0],T[-1]],[0,0],'k-')
        pylab.plot([0,0],[-0.5, 1],'k-')
        pylab.axis([T[0],T[-1],-0.5,1.1])
        
        pylab.xlabel('delay (ms)')
        pylab.ylabel('autocorrelation')
        
        
    with r.data_pylab('various') as pylab:
        pylab.plot(T, mean_xcorr, 'gx-', label='mean')
        pylab.plot(T, min_xcorr, 'bx-', label='min')
        pylab.plot(T, max_xcorr, 'rx-', label='max')
        
        pylab.plot([T[0],T[-1]],[0,0],'k-')
        pylab.plot([0,0],[-0.5, 1],'k-')
        pylab.axis([T[0],T[-1],-0.5,1.1])
        
        pylab.xlabel('delay (ms)')
        pylab.ylabel('autocorrelation')
        pylab.legend()
        
    f = r.figure()
    f.sub('some', caption='Autocorrelation of some receptors')
    f.sub('mean_xcorr', caption='Mean autocorrelation')
    
    f.sub('various', caption='Mean,min,max')
    
    filename = os.path.join(outdir, r.id + '.html')
    resources = os.path.join(outdir, 'images')
    print 'Writing to %s' % filename
    r.to_html(filename, resources)
    
    return r


         
def compute_environment_autocorrelation(db, samples, image, maxlag=50):
    nsensors = 1398
    results = numpy.ndarray(shape=(nsensors, 2*maxlag+1))
    
    db = FlydraDB(db, create=False)
    
    block_size = 50
    num_blocks = int(numpy.ceil(nsensors *1.0 / block_size))
    for b in range(num_blocks):
        start = block_size * b
        stop = min(start + block_size, nsensors)
        
        progress('Computing autocorrelation', (b, num_blocks))
         
        data = [[] for i in range(nsensors)]
        
        for k, sample in enumerate(samples):
            progress('getting data', (k, len(samples)), sample)
            table = db.get_table(sample, image)
        
            chunk = (table[:]['value'][:,start:stop]).copy()
            for j, i in enumerate(range(start, stop)): 
                data[i].append(chunk[:,j])
            
            db.release_table(table)
            
        for j, i in enumerate(range(start, stop)):
            progress('Computing correlation', (j, stop-start) )
            x = numpy.concatenate(data[i])
            corr, lags = xcorr(x, maxlag=maxlag)
            assert(len(lags) == 2*maxlag+1)
            results[i,:] = corr
        
    db.close()
    
    data = {
        'results': results,
        'lags': lags
    }
    
    return data
    
if __name__ == '__main__':
    main()                                     
    