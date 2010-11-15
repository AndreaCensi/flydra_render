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
    f = n.figure(shape=(3, 3))
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

def add_comparisons(all_experiments, outdir): 
        
    
    r = Report('comparisons')

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
        
        
        f = generic.figure(shape=(3, 2))
        f.sub('real_traj', caption='signal over all trajectory (real)')
        f.sub('hall_traj', caption='signal over all trajectory (hallucinated)')
        f.sub('diff_traj_plot', caption='real - hallucination')
        f.sub('diff_traj', caption='real - hallucination')
        
    for view, dir in prod(['start' ],   ['left', 'right']):
        # statistics over the whole trajectory
        
        
        key = Exp(image='contrast_w', group='posts', view=view, dir=dir)
        real = all_experiments[key]
        
        key = Exp(image='hcontrast_w', group='noposts', view=view, dir=dir)
        hall = all_experiments[key]
         
        
        case = r.node('analysis_%s_%s' % (view, dir))
        
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

    
        f = case.figure(shape=(3, 2))
        case = " (%s, %s)" % (dir, view)
        f.sub('real', caption='real response' + case)
        f.sub('hall', caption='hallucinated response' + case)
        f.sub('mean', caption='mean comparison' + case)
        f.sub('var', caption='variance comparison' + case)
        f.sub('linear-fit', caption='Linear fit between the two (a=%f, b=%f)' % (ar, br))
        f.sub('diff', caption='difference (real - hallucinated)' + case)
        f.sub('diffr', caption='difference (real*a- hallucinated)' + case)
        f.sub('diffn', caption='Normalized difference' + case)
        f.sub('diffn_plot', caption='Normalized difference' + case)
        f.sub('diffn_plot', caption='Normalized difference' + case)
        
        f.sub('real_minus_traj', 'Difference between saccading and trajectory (real)' + case)
        f.sub('hall_minus_traj', 'Difference between saccading and trajectory (hall)' + case)
        f.sub('rmt_minus_hmt', 'diff-diff')
    output_file = os.path.join(outdir, '%s.html' % r.id)
    resources_dir = os.path.join(outdir, 'images')
    r.to_html(output_file, resources_dir=resources_dir) 
 

Stats = namedtuple('Stats', 'mean var min max')

def compute_saccade_stats(flydra_db_directory, samples, image, conditions):
    '''
    Computes the stats of an image for the saccades that respect a 
    set of conditions.
     
    db: FlydraDB directory
    samples: list of IDs
    
    condition: saccade table -> true/false selector
    '''
    with safe_flydra_db_open(flydra_db_directory) as db:
        
        def data_pass(name):
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
                    yield id, values
                
                num_saccades += len(select)
                num_selected += (select * 1).sum()
                db.release_table(data)
                db.release_table(saccades_table)
            ratio = 100.0 / num_saccades * num_selected
            print "Selected %.2f %% of saccades" % ratio
    
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
    
        group_mean = group_mean.get_value()
    
        group_var = Expectation() 
        progress('Computing stats', (1, 2), 'Second pass')
        for sample, values in data_pass('computing var'): #@UnusedVariable
            err = values - group_mean
            sample_var = numpy.mean(numpy.square(err), axis=0)
            group_var.update(sample_var, len(values))
        group_var = group_var.get_value()
        
        result = Stats(mean=group_mean, var=group_var,
                       min=group_min, max=group_max)
        
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
    
        group_mean = group_mean.get_value()
    
        group_var = Expectation() 
        progress('Computing stats', (1, 2), 'Second pass')
        for sample, values in data_pass('computing var'): #@UnusedVariable
            err = values - group_mean
            sample_var = numpy.mean(numpy.square(err), axis=0)
            group_var.update(sample_var, len(values))
        group_var = group_var.get_value()
        
        return Stats(mean=group_mean, var=group_var,
                       min=group_min, max=group_max)
        
        
