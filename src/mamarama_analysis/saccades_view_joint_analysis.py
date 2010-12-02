import sys, os, numpy
from optparse import OptionParser
from collections import namedtuple
from itertools import product as prod 

from reprep import Report
from compmake import comp, compmake_console, set_namespace, \
                     batch_command, progress, parse_job_list

from flydra_db import FlydraDB

# XXX: put this into reprep?
from saccade_analysis.analysis201009.master_plot_gui import create_gui_new
 
from . import logger
from .covariance import Expectation


from .saccades_view_joint_analysis_data import safe_flydra_db_open, \
                                              saccades_iterate_image
from .saccades_view_joint_analysis_lasvegas import las_vegas_report, \
                                                   bet_on_flies
from .saccades_view_joint_analysis_reputils import add_scaled, add_posneg


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
    Option('allsac', 'All saccades', choose_all_saccades),
    Option('center', 'Saccades < 0.5m from center', choose_saccades_center),
    Option('border', 'Saccades > 0.5m from center', choose_saccades_border),
]


dirs = [ 
    Option('alldir', 'both', choose_all_saccades),
    Option('right', 'right', choose_saccades_right),
    Option('left', 'left', choose_saccades_left),
]

def make_page_id(image, group, saccades_set, dir):
    return "%s.%s.%s.%s" % (image, group, saccades_set, dir)

menus = [
    ('image', 'Stimulus', [(x.id, x.desc) for x in images]),
    ('group', 'Sample group', [(x.id, x.desc) for x in groups]),
    ('saccades_set', 'Saccade position', [(x.id, x.desc) for x in saccades_sets]),
    ('dir', 'Saccade direction', [(x.id, x.desc) for x in dirs]),
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
        tables = ["saccades_view_%s_%s" % (view.id, image.id) for view in views]
 
        all_available = [x for x in db.list_samples() if db.has_saccades(x) and 
                          all([db.has_table(x, table) for table in tables])] 
        
        # We further divide these in post and nopost
        groups_samples = {
            'posts':
                filter(lambda s: db.get_attr(s, 'stimulus') != 'nopost', all_available),
            'noposts':
                filter(lambda s: db.get_attr(s, 'stimulus') == 'nopost', all_available)
        }
        
        # now, for each group
        for group in groups:
             
            is_hallucination = image.id.startswith('h')
            white_arena = image.id.endswith('_w') 
        
            if (not is_hallucination) and white_arena and (group.id == 'noposts'):
                # if there are not posts, it's useless 
                continue
        
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
                    view2result[view.id] = result
          
                page_id = make_page_id(image=image.id, group=group.id,
                           dir=direction.id, saccades_set=saccades_set.id)
                
                comp(render_page, view2result, outdir, page_id, job_id=page_id)
            
            for saccades_set in saccades_sets:
                table = "saccades_view_start_%s" % (image.id)
                exp_id = '%s_%s_%s' % (image.id, group.id, saccades_set.id)
                
                results = comp(bet_on_flies, options.db, samples, table, saccades_set,
                               job_id='lasvegas-'+ exp_id + '-bet')
                page_id = exp_id
                comp(las_vegas_report, os.path.join(outdir, 'lasvegas'), page_id, results,
                              job_id='lasvegas-'+exp_id + '-report')
            
            
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
    mean_max = max(map(lambda x: numpy.max(x[1].mean), iterate_views()))
    var_max = max(map(lambda x: numpy.max(x[1].var), iterate_views()))
             
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
    



def compute_projection(x, base):
    ''' Computes projection of x onto base. 
    
        returns  (proj, err, alpha)
        such that proj = alpha * base 
        and proj + err  = x
    
    '''
    
    dot_product = lambda a, b : numpy.sum(a * b)
    
    alpha = dot_product(x , base) / dot_product(base, base)
     
    
    proj = alpha * base
    
    err = x - proj
    
    return proj, err , alpha


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
    
    
        max_value = numpy.max(numpy.max(real.var),
                              numpy.max(hall.var))
        add_scaled(case, 'real_var', real.var, max_value=max_value)
        add_scaled(case, 'hall_var', hall.var, max_value=max_value)
    
        
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
        f.sub('real', caption='real response (mean)' + cased)
        f.sub('hall', caption='hallucinated response (mean)' + cased)
        f.sub('real_var', caption='real response (var)' + cased)
        f.sub('hall_var', caption='hallucinated response (var)' + cased)
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
        
        
        proj, err, alpha = compute_projection(real.mean, hall.mean)
        
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
        rel = real_ratio - hall_ratio
        
        a = add_posneg(case, 'real_ratio', (real_ratio))
        b = add_posneg(case, 'hall_ratio', (hall_ratio))
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
        iter =  saccades_iterate_image('computing mean', 
                                       db, samples, image, conditions)
        for sample, sample_saccades, values in iter: #@UnusedVariable 
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
        iter = saccades_iterate_image('computing var', 
                                      db, samples, image, conditions)
        for sample, sample_saccades, values in iter: #@UnusedVariable
            err = values - group_mean
            sample_var = numpy.mean(numpy.square(err), axis=0)
            group_var.update(sample_var, len(values))
        group_var = group_var.get_value()
        
        result = Stats(mean=group_mean, var=group_var,
                       min=group_min, max=group_max, nsamples=num_samples)
        
        return result 


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
        
        
