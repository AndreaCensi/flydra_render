import numpy
from mamarama_analysis.saccades_view_joint_analysis_data import safe_flydra_db_open, \
    saccades_iterate_image
from compmake.jobs.progress import progress
from reprep import Report
from mamarama_analysis.saccades_view_joint_analysis_reputils import add_posneg
import os
import scipy.stats
from mamarama_analysis.covariance import Expectation

def bet_on_flies(flydra_db_directory, samples, image, saccades_set):
    
    kernels = {}
    for degrees in [15, 30, 45, 60, 90, 180]:
        # kernels['mf%d' % degrees] = create_matched_filter(degrees, [-45, 0], False)
        kernels['mf%d' % degrees] = create_matched_filter(degrees, [-20, 20], False)

        #kernels['pf%d' % degrees] = create_matched_filter(degrees, True)
         
    results = {}
    with safe_flydra_db_open(flydra_db_directory) as db:
        conditions = [saccades_set.args]
        
        # looking for the optimal dividing plane
        ex = {-1: Expectation(), +1: Expectation()}
        for sample, sample_saccades, image_values in saccades_iterate_image(#@UnusedVariable
                'computing optimal kernel', db, samples, image, conditions):
            for s in [-1, +1]:
                values = image_values[sample_saccades['sign'] == s]
                ex[s].update(values.mean(axis=0), len(values))
        
        kernels['optimal'] = ex[+1].get_value() - ex[-1].get_value()  
    
        for i, kernel_name in enumerate(kernels.keys()):            
            progress('betting', (i, len(kernels)), kernel_name)
            kernel = kernels[kernel_name]
            signs = []
            response = []
            for sample, sample_saccades, image_values in saccades_iterate_image(#@UnusedVariable
                'computing response', db, samples, image, conditions):
                    
                s = sample_saccades[:]['sign']
                    
                signs.extend(s)
                
                for i in range(len(image_values)): 
                    response.append((image_values[i, :] * kernel).sum())  
        
            signs = numpy.array(signs)
            response = numpy.array(response)
            results[kernel_name] = { 'signs': signs, 'response': response,
                                     'kernel': kernel} 
            
           

    return results

def las_vegas_report(outdir, page_id, results):
    # threshold for considering 0 response
    #eps = 0.0001
    eps = 0.001
    # eps = 0
    
    r = Report('lasvegas_' + page_id)    
    f = r.figure('summary', cols=4, caption='Response to various filters')
    
    kernels = sorted(results.keys())
    for kernel in kernels:
        sign = results[kernel]['signs']
        response = results[kernel]['response']
        matched_filter = results[kernel]['kernel']
        
        left = numpy.nonzero(sign == +1)
        right = numpy.nonzero(sign == -1)
        
        response_right = response[right]
        response_left = response[left]
        
        n = r.node(kernel)
        
        with n.data_pylab('response') as pylab:

            try:
                b = numpy.percentile(response_left, 95) #@UndefinedVariable
            except:
                b = scipy.stats.scoreatpercentile(response_left, 95)
                        
            def plothist(x, nbins, **kwargs):
                nz, = numpy.nonzero(numpy.abs(x) > eps)
                # x with nonzero response
                print "using %d/%d" % (len(nz), len(x))
                xnz = x[nz]
                hist, bin_edges = numpy.histogram(xnz, range=(-b, b), bins=nbins)
                bins = (bin_edges[:-1] + bin_edges[1:]) * 0.5
                pylab.plot(bins, hist, **kwargs)
                
            nbins = 500
            plothist(response_left, nbins, label='left')
            plothist(response_right, nbins, label='right')

            a = pylab.axis()
            pylab.axis([-b, b, 0, a[-1]])
            pylab.legend()
            
        f.sub('%s/response' % kernel)
        
        def perc(x):
            pos, = numpy.nonzero(x)
            n = len(pos)
            p = 100.0 * n / len(x)
            return "%.1f" % p
        
        cols = ['probability', 'no response', 'guessed L', 'guessed R']
        rows = ['left saccade', 'right saccade']
        table = [
            [ perc(sign == +1), perc(numpy.abs(response_left) < eps),
                              perc(response_left > eps),
                              perc(response_left < -eps) ],
            [ perc(sign == -1), perc(numpy.abs(response_right) < eps),
                              perc(response_right > eps),
                              perc(response_right < -eps) ],
        ]
        
        n.table('performance', data=table, rows=rows, cols=cols)
        
        add_posneg(n, 'kernel', matched_filter)
        
       
    output_file = os.path.join(outdir, '%s.html' % r.id)
    resources_dir = os.path.join(outdir, 'images')
    print("Writing to %s" % output_file)
    r.to_html(output_file, resources_dir=resources_dir) 



def create_matched_filter(degrees, elevation=[], pure_eye=False):
    ''' Elevation = tuple with lower and upper bound for sensor elevation (deg) '''
    n = 1398
    f = numpy.zeros((n,))
    from flydra_render.receptor_directions_buchner71 import directions 
    for i, s in enumerate(directions):
        angle = numpy.arctan2(s[1], s[0])
        phi = numpy.arcsin(s[2])
        
        if not (elevation[0] <= numpy.degrees(phi) <= elevation[1]):
            continue
        
        if pure_eye:
            eye = -numpy.sign(i - (n / 2))
            
            if numpy.abs(angle) < numpy.radians(degrees) \
               and eye == numpy.sign(angle): 
                f[i] = numpy.sign(angle)
        else:
            if numpy.abs(angle) < numpy.radians(degrees):
                f[i] = numpy.sign(angle)
                
                
    return f


