import sys, os
import numpy
from optparse import OptionParser

from reprep import Report
from reprep.graphics.posneg import posneg
from reprep.graphics.scale import scale
from compmake import comp, compmake_console, comp_prefix, set_namespace, \
    batch_command

from flydra_db import FlydraDB

from procgraph_flydra.values2retina import values2retina, add_reflines

from mamarama_analysis import logger
from mamarama_analysis.covariance import Expectation
from compmake.jobs.syntax.parsing import parse_job_list
from compmake.jobs.progress import progress

from collections import namedtuple

# describes an experiment
Exp = namedtuple('Exp', 'image group view dir')

description = """

    This program computes the statistics for the visual input
    at saccades time.  

"""

def main():
    parser = OptionParser()

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


    db = FlydraDB(options.db, False)
        
    set_namespace('saccade_view_joint_analysis')
    
    images = ['luminance', 'contrast', 'hluminance', 'hcontrast',
              'luminance_w', 'contrast_w', 'hluminance_w', 'hcontrast_w']
    
    # for each image we do a different report
    data = {}
    for image in images:
        
        # For each image we have different tables
        views = ['start', 'stop', 'rstop', 'random']
        tables = map(lambda x: "saccades_view_%s_%s" % (x, image), views)

        # We find the sample which have all of those tables
        check_available = lambda x: db.has_saccades(x) and \
            all(map(lambda table: db.has_table(x, table), tables))
        all_available = filter(check_available, db.list_samples()) 
        
        # We further divide these in post and nopost
        groups = {}
        groups['posts'] = filter(
            lambda s: db.get_attr(s, 'stimulus') != 'nopost',
                                 all_available)
        groups['noposts'] = filter(
            lambda s: db.get_attr(s, 'stimulus') == 'nopost',
                                 all_available)
                
        # now, for each group
        for group_name, group_samples in groups.items():
            
            if not group_samples:
                print "Warning: no samples for %s/%s" % (image, group_name)
                continue 
            
            # global statistics
            key = (group_name, image)
            job_id = "%s-%s" % key
            data[key] = comp(compute_stats, options.db,
                             group_samples, image, job_id=job_id)

            for i, view in enumerate(views):                
                table = tables[i]
                
                for dir, func in [('alldir', choose_all_saccades),
                                  ('right', choose_saccades_right),
                                  ('left', choose_saccades_left)]: 
                    key = Exp(image=image, group=group_name,
                              view=view, dir=dir)
                    job_id = "%s-%s-%s-%s" % key
                    data[key] = \
                        comp(compute_saccade_stats, options.db,
                            group_samples, table, func, job_id=job_id)
                
            
    comp_prefix()
    outdir = os.path.join(options.db, 'out/saccade_view_joint_analysis')
    
    comp(add_comparisons, data, outdir)
        
    db.close()
    
    if options.interactive:
        # start interactive session
        compmake_console()
    else:
        # batch mode
        # try to do everything
        batch_command('make all')
        # start the console if we are not done
        # (that is, make all failed for some reason)
        todo = list(parse_job_list('todo')) 
        if todo:
            logger.info('Still %d jobs to do.' % len(todo))
            sys.exit(-2)    
#
#
#def create_report(image_name, group_name, data):
#    r = Report('%s_%s' % (image_name, group_name))
#    # general description
#    s = ""
#    data = dict(**data) 
#    
#    data['stop_minus_start'] = data['mean_stop']['all'] - data['mean_start']['all']
#    data['rstop_minus_start'] = data['mean_rstop']['all'] - data['mean_start']['all']
#    data['rstop_minus_stop'] = data['mean_rstop']['all'] - data['mean_stop']['all']
#    data['random_minus_rstop'] = data['mean_random']['all'] - data['mean_rstop']['all']
#    
#    for a in ['start', 'stop', 'rstop']:
#        data['%s_minus_random' % a ] = \
#            data['mean_%s' % a]['all'] - data['mean_random']['all']
#
#
#    keys = ['mean_start', 'mean_stop', 'mean_rstop', 'mean_random']
#    max_value = numpy.max(map(lambda x: numpy.max(data[x]['all']), keys))
#    s += """
#    Max value for mean: %f
#    """ % max_value
#    
#    #max_value = 0.025
#    
#    for k in keys:
#        val = data[k]['all']
#        val = val / val.sum()
#        
#        r.data(k , val).data_rgb('retina',
#     #       add_reflines(scale(values2retina(val), max_value=max_value)))
#            add_reflines(scale(values2retina(val))))
#    
#        s += "%s: max %f  sum %f\n\n" % (k, val.max(), val.sum())
#    
#        for d in ['left', 'right']:
#            kd = k + '_' + d
#            val = data[kd]['all']
#            val = val / val.sum()
#                
#            s += "%s: max %f  sum %f\n\n" % (kd, val.max(), val.sum())
#            
#            r.data(kd , val).data_rgb('retina',
#              add_reflines(scale(values2retina(val))))
#    
#    
#    s += """
#    Used max value for mean: %f
#    """ % max_value
#    
#
#    keys = ['var_start', 'var_stop', 'var_rstop', 'var_random']
#    keys = keys + map(lambda s: s + '_left', keys) + map(lambda s: s + '_right', keys)
#    max_value = numpy.max(map(lambda x: numpy.max(data[x]['all']), keys))
#    for k in keys:
#        val = data[k]['all']
#        r.data(k, val).data_rgb('retina',
#            add_reflines(scale(values2retina(val), max_value=max_value)))
#    
#    s += """
#    Max value for var: %f
#    """ % max_value
#    
#
#
#    keys = ['start_minus_random', 'stop_minus_random', 'rstop_minus_random',
#            'stop_minus_start', 'rstop_minus_start', 'rstop_minus_stop']
#    for k in keys:
#        val = data[k]  
#        r.data(k, val).data_rgb('retina',
#            add_reflines(posneg(values2retina(val))))
#        
#    r.text('description', s)
#    
#    f = r.figure(shape=(3, 4))
#    f.sub('mean_start', 'Mean %s at saccade start' % image_name)
#    f.sub('mean_stop', 'Mean %s at saccade stop' % image_name)
#    f.sub('mean_rstop', 'Mean %s at random stop' % image_name)
#    f.sub('mean_random', 'Mean %s at random direction' % image_name)
#    f.sub('var_start', 'Variance %s at saccade start' % image_name)
#    f.sub('var_stop', 'Variance %s at saccade stop' % image_name)
#    f.sub('var_rstop', 'Variance %s at random stop' % image_name)
#    f.sub('var_random', 'Variance %s at random direction' % image_name)
#    f.sub('stop_minus_start')
#    f.sub('rstop_minus_start')
#    f.sub('rstop_minus_stop')
#    f.sub('start_minus_random')
#    f.sub('stop_minus_random')
#    f.sub('rstop_minus_random')
#    
#    f = r.figure(shape=(3, 2))
#    f.sub('mean_start_left', 'Mean %s at saccade start, turning left' % image_name)
#    f.sub('mean_start_right', 'Mean %s at saccade start, turning right' % image_name)
#    f.sub('mean_stop_left', 'Mean %s at saccade stop, having turned left' % image_name)
#    f.sub('mean_stop_right', 'Mean %s at saccade stop, having turned right' % image_name)
#    
##    
##    fall = r.figure('samples', shape=(3, 4))
##    for id, value in  data['mean_random']['samples'].items():
##        r.data_rgb('random-%s' % id, scale(values2retina(value)))
##        fall.sub('random-%s' % id)
#
#    return r

def add_comparisons(all_experiments, outdir): 
    
    r = Report('comparisons')
    
    for dir in ['alldir', 'left', 'right']:
        # statistics over the whole trajectory
        key = ('posts', 'contrast_w')
        real_traj = all_experiments[key]
        key = ('noposts', 'hcontrast_w')
        hall_traj = all_experiments[key]
        
        key = Exp(image='contrast_w', group='posts', view='start', dir=dir)
        real = all_experiments[key]
        
        key = Exp(image='hcontrast_w', group='noposts', view='start', dir=dir)
        hall = all_experiments[key]
        
        
        
        case = r.node('analysis_%s' % dir)
        
        diff = real.mean - hall.mean
        
        case.data('real_traj', real.mean).data_rgb('retina',
                add_reflines(scale(values2retina(real_traj.var))))
        
        case.data('hall_traj', real.mean).data_rgb('retina',
                add_reflines(scale(values2retina(hall_traj.var))))

        case.data('real', real.mean).data_rgb('retina',
                add_reflines(scale(values2retina(real.mean))))
        
        case.data('hall', real.mean).data_rgb('retina',
                add_reflines(scale(values2retina(hall.mean))))
        
        case.data('diff', diff).data_rgb('retina',
                add_reflines(posneg(values2retina(diff))))
        
        from scipy import polyfit
        (ar, br) = polyfit(real.mean, hall.mean, 1)
        case.text('case', 'Best linear fit: a = %f, b = %f.' % (ar, br))
        
        diffr = (ar * real.mean + br) - hall.mean
        case.data('diffr', diff).data_rgb('retina',
                add_reflines(posneg(values2retina(diffr))))
        
        diffn = diff / numpy.sqrt(hall.var)
        case.data('diffn', diffn).data_rgb('retina',
                add_reflines(posneg(values2retina(diffr))))
        
        
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
        f.sub('real_traj', caption='mean over all trajectory (real)')
        f.sub('hall_traj', caption='mean over all trajectory (hallucinated)')
        f.sub('real', caption='real response')
        f.sub('hall', caption='hallucinated response')
        f.sub('mean', caption='mean comparison')
        f.sub('var', caption='variance comparison')
        f.sub('linear-fit', caption='Linear fit between the two (a=%f, b=%f)' % (ar, br))
        f.sub('diff', caption='difference (real - hallucinated)')
        f.sub('diffr', caption='difference (real*a- hallucinated)')
        f.sub('diffn', caption='Normalized difference')
        
    output_file = os.path.join(outdir, '%s.html' % r.id)
    resources_dir = os.path.join(outdir, 'images')
    r.to_html(output_file, resources_dir=resources_dir)
#    
#
#def write_report(reports, outdir, page_id):
#    output_file = os.path.join(outdir, page_id + '.html')
#    resources_dir = os.path.join(outdir, 'images')
#    
#        
#    r = Report(page_id, children=reports)
#    
#    print "Writing to %s" % output_file
#    r.to_html(output_file, resources_dir=resources_dir)
 

Stats = namedtuple('Stats', 'mean var min max')

def compute_saccade_stats(db, samples, image, condition):
    '''
    Computes the stats of an image for the saccades that respect a condition.
     
    db: FlydraDB directory
    samples: list of IDs
    
    condition: saccade table -> true/false selector
    '''
    db = FlydraDB(db, False) 
    
    def data_pass(name):
        for i, id in enumerate(samples):
            progress(name, (i, len(samples)), "Sample %s" % id)
        
            if not db.has_saccades(id):
                raise ValueError('No saccades for %s' % id)
            if not (db.has_sample(id) and db.has_table(id, image)):
                raise ValueError('No table "%s" for id %s' % (image, id))
            
            saccades = db.get_saccades(id)
            data = db.get_table(id, image)
            
            select = condition(saccades)
            values = data[select]['value']
            
            yield id, values
            db.release_table(data)
            db.release_table(saccades)

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
    db.close()
    
    return result 

def choose_saccades_right(saccades):
    return saccades[:]['sign'] == -1

def choose_saccades_left(saccades):
    return saccades[:]['sign'] == +1

def choose_all_saccades(saccades):
    return saccades[:]['sign'] != 0



def compute_stats(db, samples, image):
    '''
    Computes the stats of an image.
    
    *db*
      FlydraDB directory
    
    *samples*
      list of IDs
      
    image: name of a table
    '''
    db = FlydraDB(db, False) 
    
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
    
    result = Stats(mean=group_mean, var=group_var,
                   min=group_min, max=group_max)
    db.close()
    
    return result 
