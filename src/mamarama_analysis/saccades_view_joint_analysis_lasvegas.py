import numpy, os, scipy.stats, cPickle
from scipy.stats.morestats import binom_test

from compmake  import progress
from reprep import Report
from flydra_db import safe_flydra_db_open

from .saccades_view_joint_analysis_data import  saccades_iterate_image
from .saccades_view_joint_analysis_reputils import add_posneg
from .covariance import Expectation


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
                
                if len(values) > 0:
                    ex[s].update(values.mean(axis=0), len(values))
        
        kernels['optimal'] = ex[+1].get_value() - ex[-1].get_value()  
    
        dir = '${SNPENV_DATA}/flydra_db/out/saccade_view_joint_analysis/lasvegas/images/'
        others = {
         'center': 'lasvegas_contrast_w_posts_center:optimal:kernel.pickle',
         'border': 'lasvegas_contrast_w_posts_border:optimal:kernel.pickle',
         'allsac': 'lasvegas_contrast_w_posts_allsac:optimal:kernel.pickle'
        }
        
        for name, f in others.items():
            filename = os.path.expandvars(os.path.join(dir, f))
            kernel = cPickle.load(open(filename, 'rb'))
            #mask_deg = create_matched_filter(75, [-60, 60],True)
            mask_deg = create_matched_filter(75, [-90, 90], True)
            kernel = kernel * numpy.abs(mask_deg)
            
            kernels['common_%s' % name] = kernel
            
    
        
        for i, kernel_name in enumerate(kernels.keys()):            
            progress('betting', (i, len(kernels)), kernel_name)
            kernel = kernels[kernel_name]
            
            signs = []
            response = []
            overlap = []
            for sample, sample_saccades, image_values in saccades_iterate_image(#@UnusedVariable
                'computing response', db, samples, image, conditions):
                    
                s = sample_saccades[:]['sign']
                    
                signs.extend(s)
                
                for i in range(len(image_values)): 
                    
                    response_i = (image_values[i, :] * kernel).sum()
                    response.append(response_i)
                    
                    overlap_i = (image_values[i, :] * 
                                    numpy.abs(kernel)).sum()
                    overlap.append(overlap_i)
        
            signs = numpy.array(signs)
            response = numpy.array(response)
            results[kernel_name] = { 'signs': signs, 'response': response,
                                     'kernel': kernel, 'overlap': overlap} 
            

    return results

try:
    percentile = numpy.percentile
except:
    percentile = scipy.stats.scoreatpercentile

                   

def las_vegas_report(outdir, page_id, results):
    # threshold for considering 0 response
    #eps = 0.0001
    # eps = 0.001
    # eps = 0
    
    r = Report('lasvegas_' + page_id)    
    f = r.figure('summary', cols=4, caption='Response to various filters')
    f_overlap = r.figure('summary-overlap', cols=4,
                         caption='Response area (overlap) of various filters')
    
    kernels = sorted(results.keys())
    for kernel in kernels:
        sign = results[kernel]['signs']
        response = results[kernel]['response']
        # overlap = results[kernel]['overlap']
        overlap = numpy.abs(response)
        
        eps = percentile(overlap, 75)
        
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
                        
            def plothist(x, nbins, eps, **kwargs):
                nz, = numpy.nonzero(numpy.abs(x) > eps)
                # x with nonzero response
                print "using %d/%d" % (len(nz), len(x))
                xnz = x[nz]
                hist, bin_edges = numpy.histogram(xnz, range=(-b, b), bins=nbins)
                bins = (bin_edges[:-1] + bin_edges[1:]) * 0.5
                pylab.plot(bins, hist, **kwargs)
                
            nbins = 500
            plothist(response_left, nbins, eps, label='left')
            plothist(response_right, nbins, eps, label='right')

            a = pylab.axis()
            pylab.axis([-b, b, 0, a[-1]])
            pylab.legend()
            
        f.sub('%s/response' % kernel)
        
        with n.data_pylab('overlap') as pylab:

            def plothist2(x, nbins, **kwargs):
                hist, bin_edges = numpy.histogram(x, bins=nbins)
                bins = (bin_edges[:-1] + bin_edges[1:]) * 0.5
                pylab.plot(bins, hist, **kwargs)
                
            nbins = 200
            
            # plothist2(overlap, nbins, label='overlap')
            pylab.hist(overlap, nbins, log=True, label='hist of abs.response')

            a = pylab.axis()
            pylab.plot([ eps, eps], [a[2], a[3]], 'r-', label='threshold')
            #pylab.axis([-b, b, 0, a[-1]])
            pylab.legend()
            
        f_overlap.sub('%s/overlap' % kernel)
        
        def ratio2perc(i, n):
            p = 100.0 * i / n
            return "%.1f" % p
        
        def perc(x):
            pos, = numpy.nonzero(x)
            return ratio2perc(len(pos), len(x))
        
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
        
        use_eps = eps
        total = len(sign)
        given = numpy.abs(response) > use_eps
        num_given = len(numpy.nonzero(given)[0])
        correct = numpy.logical_or(
                numpy.logical_and(response > use_eps, sign == +1),
                numpy.logical_and(response < -use_eps, sign == -1)
        )
        
        num_correct = len(numpy.nonzero(correct)[0])
        
        perc_given = ratio2perc(num_given, total)
        perc_not_given = ratio2perc(len(sign) - num_given, len(sign))
        
    #    perc_correct_abs =  ratio2perc(num_correct, total) 
        
        perc_correct_given = ratio2perc(num_correct, num_given)
        
        signif = 0.01
        expected = \
            scipy.stats.binom.ppf([signif / 2, 1 - signif / 2], num_given, 0.5) / num_given
        #cdf = scipy.stats.binom.cdf(perc_correct_given, num_given, 0.5)
        pvalue = binom_test(num_correct, num_given, 0.5)
        
        cols = ['no response', 'with response',
                'correct (%given)', 'p-value', 'bounds under H0']
        table = [
            [ perc_not_given, perc_given,
               perc_correct_given,
              "%.4f" % pvalue,
              "[%.1f, %.1f]" % (100 * expected[0], 100 * expected[1]) ],
              
        ]
        
        n.table('performance2', data=table, cols=cols)
       
        
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


