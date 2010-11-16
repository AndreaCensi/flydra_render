import sys, os
import numpy
from optparse import OptionParser

from reprep import Report
from reprep.graphics.posneg import posneg
from reprep.graphics.scale import scale
from compmake import comp, compmake_console, set_namespace, batch_command, progress

from flydra_db import FlydraDB

from procgraph_flydra.values2retina import values2retina, add_reflines

from mamarama_analysis import logger
from mamarama_analysis.covariance import Expectation
from compmake.jobs.syntax.parsing import parse_job_list

from collections import namedtuple
from itertools import product as prod
from saccade_analysis.tammero.tammero_analysis import add_position_information
from contextlib import contextmanager

from saccade_analysis.analysis201009.master_plot_gui import create_gui_new

def choose_saccades_right(saccades):
    return saccades[:]['sign'] == -1

def choose_saccades_left(saccades):
    return saccades[:]['sign'] == +1

def choose_all_saccades(saccades):
    return saccades[:]['sign'] != 0

def choose_saccades_center(saccades):
    return saccades['distance_from_center'] < 0.5

def choose_saccades_border(saccades):
    return saccades['distance_from_center'] >= 0.5

# describes an experiment
Exp = namedtuple('Exp', 'image group view dir saccades_set')

class Option:
    def __init__(self, id, desc=None, args=None):
        self.id = id
        self.desc = desc
        self.args = args

images = [
        Option('luminance', 'Raw luminance'),
        Option('luminance_w', 'Raw luminance (only posts)'),
        Option('contrast', 'Contrast'),
        Option('contrast_w', 'Contrast (only posts)'),
        Option('hluminance', 'Hallucinated raw luminance'),
        Option('hluminance_w', 'Hallucinated raw luminance (only posts)'),
        Option('hcontrast', 'Hallucinated contrast'),
        Option('hcontrast_w', 'Hallucinated contrast (only posts)')
]

views = [
    Option('start', 'At saccade start'),
    Option('stop', 'At saccade stop'),
    Option('rstop', 'At random amplitude stop according to dist'),
    Option('sstop', 'At random amplitude stop (same sign)'),
    Option('random', 'At random orientation'),
]

groups = [
    Option('posts', 'Samples with posts'),
    Option('noposts', 'Samples without posts'),
]

saccades_sets = [
    Option('allsac', 'All saccades',  choose_all_saccades ),
    Option('center', 'Saccades < 0.5m from center', choose_saccades_center),
    Option('border', 'Saccades > 0.5m from center', choose_saccades_border),
]


dirs = [ 
    Option('alldir', 'both', choose_all_saccades),
    Option('right', 'right', choose_saccades_right),
    Option('left', 'left', choose_saccades_left),
]

def make_page_id(image,group,saccades_set,dir):
    return "%s.%s.%s.%s" % (image,group,saccades_set,dir)

menus = [
    ('image', 'Stimulus', [(x.id, x.desc) for x in images]),
    ('group', 'Sample group',  [(x.id, x.desc) for x in groups]),
    ('saccades_set', 'Saccade position',  [(x.id, x.desc) for x in saccades_sets]),
    ('dir', 'Saccade direction',  [(x.id, x.desc) for x in dirs]),
]
 

description = """

    This program computes the statistics for the visual input
    at saccades time.  

"""


    
def main():
    parser = OptionParser(usage=description)

    parser.add_option("--db", default='flydra_db', help="Data directory")

    parser.add_option("--interactive", default=False, action="store_true",
                      help="Start a compmake interactive session."
                      " Otherwise run in batch mode") 

    parser.add_option("--empty_group_ok",
                      default=False, action="store_true",
                      help="do not give up if one group does not have samples ")


    (options, args) = parser.parse_args() #@UnusedVariable
    
    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)

    outdir = os.path.join(options.db, 'out/saccade_view_joint_analysis')

    db = FlydraDB(options.db, False)
        
    set_namespace('saccade_view_joint_analysis')
    
    # for each image we do a different report
    data = {}
    for image in images:
        
        # For each image we have different tables
        tables = []
        for view in views:
            tables.append("saccades_view_%s_%s" % (view.id, image.id))

        # We find the sample which have all of those tables
        check_available = lambda x: db.has_saccades(x) and \
            all(map(lambda table: db.has_table(x, table), tables))
        all_available = filter(check_available, db.list_samples()) 
        
        # We further divide these in post and nopost
        groups_samples = {
            'posts':
                filter(lambda s: db.get_attr(s, 'stimulus') != 'nopost', all_available),
            'noposts':
                filter(lambda s: db.get_attr(s, 'stimulus') == 'nopost', all_available)
        }
        
        # now, for each group
        for group in groups:
            samples = groups_samples[group.id] 
            if not samples:
                print "Warning: no samples for %s/%s" % (image.id, group.id)
                continue 
            
            # global statistics
            key = (group.id, image.id)
            job_id = "%s-%s" % key
            data[key] = comp(compute_stats, options.db,
                             samples, image.id, job_id=job_id)

            for saccades_set, direction in prod(saccades_sets, dirs):             
                view2result = {}
                for i, view in enumerate(views):                
                    table = tables[i]
                    key = Exp(image=image.id, group=group.id,
                              view=view.id, dir=direction.id,
                              saccades_set=saccades_set.id)
                    job_id = "%s-%s-%s-%s-%s" % key
                    
                    result = comp(compute_saccade_stats, options.db,
                             samples, table, 
                             [direction.args, saccades_set.args], 
                             job_id=job_id)
                    
                    data[key] = result
                    view2result[view.id]= result
          
                page_id = make_page_id(image=image.id, group=group.id, 
                           dir=direction.id, saccades_set=saccades_set.id)
                
                comp(render_page, view2result, outdir, page_id, job_id=page_id)
            
            for saccades_set in saccades_sets:
                table = "saccades_view_start_%s" % (image.id)
                exp_id = '%s_%s_%s' % (table, group.id,  saccades_set.id)
                
                results = comp(bet_on_flies, options.db, samples, table, saccades_set,
                               job_id=exp_id+'-bet')
                page_id = exp_id
                report = comp(las_vegas_report, outdir, page_id, results,
                              job_id=exp_id+'-report')
            
            
    db.close()
    
    comp(add_comparisons, data, outdir)
    

    filename = os.path.join(outdir, 'gui.html')   
    comp(create_gui_new, filename, menus)
    
    
    if options.interactive:
        # start interactive session
        compmake_console()
    else:
        # batch mode
        # try to do everything
        batch_command('make all')
        # exit with error if we are not done
        # (that is, make all failed for some reason)
        todo = list(parse_job_list('todo')) 
        if todo:
            logger.info('Still %d jobs to do.' % len(todo))
            sys.exit(-2)    
 
def render_page(view2result, outdir, page_id):

    def iterate_views():
        for view in views: 
            yield view, view2result[view.id]
            
    # first compute max value
    mean_max = max(map(lambda x: numpy.max(x[1].mean), iterate_views()) )
    var_max = max(map(lambda x: numpy.max(x[1].var), iterate_views()) )
             
    n = Report(page_id)
    f = n.figure(cols=3)
    for view, stats in iterate_views():
        nv = n.node(view.id)
        add_scaled(nv, 'mean', stats.mean, max_value=mean_max)
        add_scaled(nv, 'var', stats.var, max_value=var_max)
        #add_scaled(nv, 'min', stats.min)
        #add_scaled(nv, 'max', stats.max)
    
    for view in views:
        what = 'mean'
    #for what, view in prod(['mean', 'var'], views):
        f.sub('%s/%s' % (view.id, what),
              caption='%s (%s)' % (view.desc, what))
    
    output_file = os.path.join(outdir, '%s.html' % n.id)
    resources_dir = os.path.join(outdir, 'images')
    print "Writing to %s" % output_file
    n.to_html(output_file, resources_dir=resources_dir)
    


def add_scaled(report, id, x, **kwargs):
    n = report.data(id, x)
    
    n.data_rgb('retina',
            add_reflines(scale(values2retina(x), min_value=0,**kwargs)))
    
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


def compute_projection(x, base):
    ''' Computes projection of x onto base. 
    
        returns  (proj, err, alpha)
        such that proj = alpha * base 
        and proj + err  = x
    
    '''
    
    dot_product = lambda a,b : numpy.sum(a*b)
    
    alpha = dot_product(x , base) / dot_product(base,base)
     
    
    proj = alpha * base
    
    err = x - proj
    
    return proj, err , alpha

def create_matched_filter(degrees, pure_eye=False):
    n = 1398
    f = numpy.zeros((n,))
    from flydra_render.receptor_directions_buchner71 import directions 
    for i, s in enumerate(directions):
        angle = numpy.arctan2(s[1],s[0])
        
        if pure_eye:
            eye = -numpy.sign(i - (n/2))
            
            if numpy.abs(angle) < numpy.radians(degrees) \
               and eye == numpy.sign(angle): 
                f[i] = numpy.sign(angle)
        else:
            if numpy.abs(angle) < numpy.radians(degrees):
                f[i] = numpy.sign(angle)
                
                
    return f

def bet_on_flies(flydra_db_directory, samples, image, saccades_set):
    
    kernels = {}
    for degrees in [15,30,45,60,90,180]:
        kernels['mf%d' % degrees] = create_matched_filter(degrees, False)
        kernels['pf%d' % degrees] = create_matched_filter(degrees, True)
        
    
    page_id = '%s-%s' % (image, saccades_set.id)

    results = {}
    
    with safe_flydra_db_open(flydra_db_directory) as db:
        conditions = [saccades_set.args]
    
        for i, kernel_name in enumerate(kernels.keys()):            
            progress('betting', (i, len(kernels)), kernel_name)
            kernel = kernels[kernel_name]
            signs = []
            response = []
            for sample, sample_saccades, image_values in \
                saccades_iterate_image('computing response', db, samples, image, conditions):
                    
                s = sample_saccades[:]['sign']
                    
                signs.extend(s)
                
                for i in range(len(image_values)): 
                    response.append( (image_values[i,:] * kernel).sum() )  
        
            signs = numpy.array(signs)
            response = numpy.array(response)
            results[kernel_name] =  { 'signs': signs, 'response': response,
                                     'kernel': kernel}    

    return results

def las_vegas_report(outdir, page_id, results):
    
    r = Report('lasvegas_'+ page_id)    
    f = r.figure('summary', cols=4,caption='Response to various filters')
    
    kernels = sorted(results.keys())
    for kernel in kernels:
        sign = results[kernel]['signs']
        response =  results[kernel]['response']
        matched_filter =  results[kernel]['kernel']
        
        left = numpy.nonzero(sign==+1)
        right = numpy.nonzero(sign==-1)
        
        response_right = response[right]
        response_left = response[left]
        
        n = r.node(kernel)
        
        with n.data_pylab('response') as pylab:

            
            b = numpy.percentile(response_left, 95)
                        
            def plothist(x, nbins, **kwargs):
                hist, bin_edges = numpy.histogram(x, range=(-b,b),bins= nbins)
                bins = (bin_edges[:-1] + bin_edges[1:]) *0.5
                pylab.plot(bins, hist, **kwargs)
                
            nbins = 500
            plothist(response_left, nbins, label='left')
            plothist(response_right,nbins,  label='right')

            a = pylab.axis()
            pylab.axis([-b,b,0,a[-1]])
            pylab.legend()
            
        f.sub('%s/response' % kernel)
        
        def perc(x):
            pos, = numpy.nonzero(x)
            n = len(pos)
            p = 100.0 * n / len(x)
            return "%.1f" % p
        
        cols = ['probability', 'no response', 'guessed L', 'guessed R']
        rows = ['left saccade', 'right saccade']
        eps = 0.0001
        table = [
            [ perc(sign==+1), perc(numpy.abs(response_left)<eps), 
                              perc(response_left>eps), 
                              perc(response_left<-eps) ],
            [ perc(sign==-1), perc(numpy.abs(response_right)<eps),
                              perc(response_right>eps), 
                              perc(response_right<-eps) ],                
        ]
        
        n.table('performance', data=table, rows=rows, cols=cols)
        
        add_posneg(n, 'kernel', matched_filter)
        
       
    output_file = os.path.join(outdir, '%s.html' % r.id)
    resources_dir = os.path.join(outdir, 'images')
    print("Writing to %s" % output_file)
    r.to_html(output_file, resources_dir=resources_dir) 

def add_comparisons(all_experiments, outdir): 
        
    r = Report('comparisons')

    fmain = r.figure('summary', cols=3, 
                     caption="Summary of projection analysis")

    n = r.node('odds analysis')
    fodds_real = n.figure('odds_real', cols=3, 
                     caption="Summary of odds analysis (real)")
    fodds_hall = n.figure('odds_hall', cols=3, 
                     caption="Summary of odds analysis (hall)")
    fodds_rel = n.figure('rel', cols=3, caption="Relative odds")

    generic = r.node('generic')
    if 1:
        key = ('posts', 'contrast_w')
        real_traj = all_experiments[key]
        key = ('noposts', 'hcontrast_w')
        hall_traj = all_experiments[key]
        diff = real_traj.mean - hall_traj.mean
        
        max_value = numpy.max(numpy.max(real_traj.mean),
                              numpy.max(hall_traj.mean))
        add_scaled(generic, 'real_traj', real_traj.mean, max_value=max_value)
        add_scaled(generic, 'hall_traj', hall_traj.mean, max_value=max_value)
        add_posneg(generic, 'diff_traj', diff)
        with generic.data_pylab('diff_traj_plot') as pylab:
            pylab.plot(real_traj.mean, 'b.', label='real')
            pylab.plot(hall_traj.mean, 'r.', label='hallucination')
        
        
        f = generic.figure(cols=2)
        f.sub('real_traj', caption='signal over all trajectory (real)')
        f.sub('hall_traj', caption='signal over all trajectory (hallucinated)')
        f.sub('diff_traj_plot', caption='real - hallucination')
        f.sub('diff_traj', caption='real - hallucination')
        
    for view, dir, saccades_set in \
        prod(['start' ],   
             ['left', 'right', 'alldir'],
             ['allsac', 'center', 'border']):
        # statistics over the whole trajectory
        
        
        key = Exp(image='contrast_w', group='posts', 
                  view=view, dir=dir, saccades_set=saccades_set)
        real = all_experiments[key]
        
        key = Exp(image='hcontrast_w', group='noposts', 
                  view=view, dir=dir, saccades_set=saccades_set)
        hall = all_experiments[key]
         
        
        case = r.node('analysis_%s_%s_%s' % (view, dir, saccades_set))
        
        cased = " (%s, %s, %s)" % (dir, view, saccades_set)
        
        diff = real.mean - hall.mean

        max_value = numpy.max(numpy.max(real.mean),
                              numpy.max(hall.mean))
        add_scaled(case, 'real', real.mean, max_value=max_value)
        add_scaled(case, 'hall', hall.mean, max_value=max_value)
        add_posneg(case, 'diff', diff)
        
        real_minus_traj = real.mean - real_traj.mean
        hall_minus_traj = hall.mean - hall_traj.mean
        rmt_minus_hmt = numpy.maximum(0, real_minus_traj) - \
                        numpy.maximum(0, hall_minus_traj)
        M = numpy.max(numpy.abs(real_minus_traj).max(),
                      numpy.abs(hall_minus_traj).max())
        add_posneg(case, 'real_minus_traj', real_minus_traj, max_value=M)
        add_posneg(case, 'hall_minus_traj', hall_minus_traj, max_value=M)
        add_posneg(case, 'rmt_minus_hmt', rmt_minus_hmt)
        
        from scipy import polyfit
        (ar, br) = polyfit(real.mean, hall.mean, 1)
        case.text('case', 'Best linear fit: a = %f, b = %f.' % (ar, br))
        
        diffr = (ar * real.mean + br) - hall.mean
        add_posneg(case, 'diffr', diffr)
        
        diffn = diff / numpy.sqrt(hall.var)
        add_posneg(case, 'diffn', diffn)
        
        with case.data_pylab('diffn_plot') as pylab:
            pylab.plot(diffn, 'k.')
        
        with case.data_pylab('linear-fit') as pylab:
            pylab.plot(real.mean, hall.mean, '.')
            pylab.plot(real.mean, real.mean, 'k.')
            
            pylab.plot(real.mean, real.mean * ar + br, 'r.')
            pylab.axis('equal')

        with case.data_pylab('mean') as pylab:
            x = range(len(real.mean))
            pylab.plot(x, real.mean, 'b.', label='real')
            pylab.plot(x, hall.mean, 'r.', label='hallucinated')
            #yerr = numpy.sqrt(var_cwnd) * 2
            #pylab.errorbar(x, cwnd, yerr=yerr, color='k', label='hallucinated')
            pylab.legend()
            pylab.title('mean')

        with case.data_pylab('var') as pylab:
            x = range(len(real.var))
            pylab.plot(x, numpy.sqrt(real.var) * 2, 'b.', label='real')
            pylab.plot(x, numpy.sqrt(hall.var) * 2, 'r.', label='hallucinated')
            pylab.legend()
            pylab.title('variance')

    
        f = case.figure(cols=2)
        f.sub('real', caption='real response' + cased)
        f.sub('hall', caption='hallucinated response' + cased)
        f.sub('mean', caption='mean comparison' + cased)
        f.sub('var', caption='variance comparison' + cased)
        f.sub('linear-fit', caption='Linear fit between the two (a=%f, b=%f)' 
              % (ar, br))
        f.sub('diff', caption='difference (real - hallucinated)' + cased)
        f.sub('diffr', caption='difference (real*a- hallucinated)' + cased)
        f.sub('diffn', caption='Normalized difference' + cased)
        f.sub('diffn_plot', caption='Normalized difference' + cased)
        f.sub('diffn_plot', caption='Normalized difference' + cased)
        
        f.sub('real_minus_traj', 
              'Difference between saccading and trajectory (real)' + cased)
        f.sub('hall_minus_traj', 
              'Difference between saccading and trajectory (hall)' + cased)
        f.sub('rmt_minus_hmt', 'diff-diff')
        
        
        proj, err, alpha =  compute_projection(real.mean, hall.mean)
        
        add_scaled(case, 'proj', proj)
        money = add_posneg(case, 'err', err)
        case.text('stats', 'alpha = %f' % alpha)
        
        f = case.figure(cols=2)
        
        f.sub('proj', caption='projection' + cased)
        f.sub('err', caption='error' + cased)
        
        fmain.sub(money, caption='mismatch' + cased)
       
       
        f = case.figure(cols=2, caption="relative odds")
        
        real_ratio = numpy.log(real.mean / real_traj.mean)
        hall_ratio = numpy.log(hall.mean / hall_traj.mean)
        rel = real_ratio -hall_ratio
        
        a = add_posneg(case, 'real_ratio', (real_ratio))
        b = add_posneg(case, 'hall_ratio',  (hall_ratio))
        c = add_posneg(case, 'rel', rel)
        
        f.sub('real_ratio', caption='real relative' + cased)
        f.sub('hall_ratio', caption='hall relative' + cased)
        f.sub('rel')
        
        fodds_real.sub(a, cased)
        fodds_hall.sub(b, cased)
        fodds_rel.sub(c, cased)
        
    output_file = os.path.join(outdir, '%s.html' % r.id)
    resources_dir = os.path.join(outdir, 'images')
    r.to_html(output_file, resources_dir=resources_dir) 
 

Stats = namedtuple('Stats', 'mean var min max nsamples')
 
def saccades_iterate_image(name, db, samples, image, conditions):
    ''' Iterates over the values of an image corresponding to
        the saccades that respect a given condition.
        
        yields  sample, saccades, image_values 
    '''
    
    num_saccades = 0
    num_selected = 0
    for i, id in enumerate(samples):
        progress(name, (i, len(samples)), "Sample %s" % id)
    
        if not db.has_saccades(id):
            raise ValueError('No saccades for %s' % id)
        if not (db.has_sample(id) and db.has_table(id, image)):
            raise ValueError('No table "%s" for id %s' % (image, id))
        
        saccades_table = db.get_saccades(id)
        
        saccades = add_position_information(saccades_table)
        
        data = db.get_table(id, image)
        
        # computes and of all conditions
        select = reduce(numpy.logical_and, 
                        map(lambda c:c(saccades), conditions))
        
        values = data[select]['value']
        
        if len(values) == 0:
            print ("No saccades selected for %s (out of %d)." % 
                   (id, len(saccades)))
        else:
            yield id, saccades[select], values
        
        num_saccades += len(select)
        num_selected += (select * 1).sum()
        db.release_table(data)
        db.release_table(saccades_table)
    ratio = 100.0 / num_saccades * num_selected
    print "Selected %.2f %% of saccades" % ratio


def compute_saccade_stats(flydra_db_directory, samples, image, conditions):
    '''
    Computes the stats of an image for the saccades that respect a 
    set of conditions.
     
    db: FlydraDB directory
    samples: list of IDs
    
    condition: saccade table -> true/false selector
    '''
    with safe_flydra_db_open(flydra_db_directory) as db:
        
        progress('Computing stats', (0, 2), 'First pass')
        # first compute the mean
        group_mean = Expectation()
        group_min = None
        group_max = None
        for sample, sample_saccades, values in\
            saccades_iterate_image('computing mean', db, samples, image, conditions):
            sample_mean = numpy.mean(values, axis=0)
            sample_min = numpy.min(values, axis=0)
            sample_max = numpy.max(values, axis=0)
            if group_min is None:
                group_min = sample_min
                group_max = sample_max
            else:
                group_min = numpy.minimum(sample_min, group_min)
                group_max = numpy.maximum(sample_max, group_max)
                
            group_mean.update(sample_mean, len(values))
    
        num_samples = group_mean.num_samples
        group_mean = group_mean.get_value()
    
        group_var = Expectation() 
        progress('Computing stats', (1, 2), 'Second pass')
        for sample, sample_saccades, values in \
            saccades_iterate_image('computing var', db, samples, image, conditions):
            err = values - group_mean
            sample_var = numpy.mean(numpy.square(err), axis=0)
            group_var.update(sample_var, len(values))
        group_var = group_var.get_value()
        
        result = Stats(mean=group_mean, var=group_var,
                       min=group_min, max=group_max, nsamples=num_samples)
        
        return result 

@contextmanager
def safe_flydra_db_open(flydra_db_directory):
    ''' Context manager to remember to close the .h5 files. '''
    db = FlydraDB(flydra_db_directory, False)
    try:
        yield db
    finally:
        db.close()

def compute_stats(flydra_db_directory, samples, image):
    '''
    Computes the stats of an image.
    
    *db*
      FlydraDB directory
    
    *samples*
      list of IDs
      
    image: name of a table
    '''
    
    with safe_flydra_db_open(flydra_db_directory) as db:
         
        def data_pass(name):
            for i, id in enumerate(samples):
                progress(name, (i, len(samples)), "Sample %s" % id)
            
                if not (db.has_sample(id) and db.has_table(id, image)):
                    raise ValueError('No table "%s" for id %s' % (image, id))
                
                rows = db.get_rows(id)
                data = db.get_table(id, image)
                
                select = rows[:]['linear_velocity_modulus'] > 0.1
                #select = condition(rows)
                values = data[select]['value']
                
                yield id, values
                db.release_table(data)
                db.release_table(rows)
    
        progress('Computing stats', (0, 2), 'First pass')
        # first compute the mean
        group_mean = Expectation()
        group_min = None
        group_max = None
        for sample, values in data_pass('computing mean'): #@UnusedVariable
            sample_mean = numpy.mean(values, axis=0)
            sample_min = numpy.min(values, axis=0)
            sample_max = numpy.max(values, axis=0)
            if group_min is None:
                group_min = sample_min
                group_max = sample_max
            else:
                group_min = numpy.minimum(sample_min, group_min)
                group_max = numpy.maximum(sample_max, group_max)
                
            group_mean.update(sample_mean, len(values))
    
        num_samples = group_mean.num_samples
        group_mean = group_mean.get_value()
    
        group_var = Expectation() 
        progress('Computing stats', (1, 2), 'Second pass')
        for sample, values in data_pass('computing var'): #@UnusedVariable
            err = values - group_mean
            sample_var = numpy.mean(numpy.square(err), axis=0)
            group_var.update(sample_var, len(values))
        group_var = group_var.get_value()
        
        return Stats(mean=group_mean, var=group_var,
                       min=group_min, max=group_max, nsamples=num_samples)
        
        
