import sys, os
import numpy
from optparse import OptionParser

from reprep import Report
from reprep.graphics.posneg import posneg
from reprep.graphics.scale import scale
from compmake import comp, compmake_console, comp_prefix, set_namespace

from flydra_render.db import FlydraDB
from procgraph_flydra.values2retina import values2retina, plot_contrast

from mamarama_analysis import logger
from mamarama_analysis.covariance import compute_image_mean, compute_image_var,\
    compute_mean_generic, array_mean, array_var

description = """

    This program computes the statistics for the visual input
    at saccades time.  

"""

def main():
    parser = OptionParser()

    parser.add_option("--db", default='flydra_db',
                      help="Data directory")

    parser.add_option("--image", default="luminance",
                      help="Rendered image to use -- "
            " corresponding to image 'saccades_view_{start,stop}_X'")

    (options, args) = parser.parse_args() #@UnusedVariable
    
    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)

    views = ['start','stop','rstop','random']
    images = map(lambda x: "saccades_view_%s_%s" % (x, options.image), views)


    db = FlydraDB(options.db)

    groups = {}
    
    # all samples with enough data
    all_available = lambda x: db.has_saccades(x) and \
        all(map(lambda table: db.has_table(x, table), images))

    
    # select with and without posts     
    posts = lambda x: all_available(x) and \
        db.get_attr(x, 'stimulus', None) != 'nopost'
    noposts = lambda x: all_available(x) and  not posts(x)
    
    def select(x):
        return set(filter(x, db.list_samples()))
    
    groups['all'] = db.list_samples()
    groups['posts'] = select(posts)
    groups['noposts'] = select(noposts)
    groups['with_data'] = select(all_available) 
    
    logger.info('Found %s samples in total; %s with data. Posts: %d; no posts: %d.' % \
                (len(groups['all']), len(groups['with_data']), len(groups['posts']),
                 len(groups['noposts'])))
    
    all_reports = []
    
    use_groups = ['posts', 'noposts']
    
    set_namespace('saccade_view_analysis_%s' % options.image)
    
    for group_name in use_groups:
        group_samples = groups[group_name]
        
        if not group_samples:
            raise Exception('Could not find any samples in group "%s".' 
                            % group_name) 
        comp_prefix(group_name) 
        
        data = {}
        
        for i in range(len(views)):
            view = views[i]
            table = images[i]
            data['mean_%s' % view] = comp(compute_mean_generic, options.db,
                        group_samples, table, array_mean)


            data['var_%s' % view] = comp(compute_mean_generic, options.db,
                        group_samples, table, array_var)

        
        report = comp(create_report, group_name, data, options.image)
        all_reports.append(report)
        
    comp_prefix()

    filename = 'out/saccade_view_analysis/%s.html' % options.image
    comp(write_report, all_reports, options.db, filename)
    compmake_console()
    
 
    

def create_report(group_name, data, image_name):
    r = Report(group_name)
    
    data = dict(**data)
    
    data['stop_minus_start'] = data['mean_stop']['all'] - data['mean_start']['all']
    data['rstop_minus_start'] = data['mean_rstop']['all'] - data['mean_start']['all']
    data['rstop_minus_stop'] = data['mean_rstop']['all'] - data['mean_stop']['all']


    keys = ['mean_start', 'mean_stop', 'mean_rstop', 'mean_random']
    max_value = numpy.max(map(lambda x: numpy.max(data[x]['all']), keys))
    for k in keys:
        val = data[k]['all']
        r.data(k , val).data_rgb('retina', scale(values2retina(val), max_value=max_value))

    keys = ['var_start', 'var_stop', 'var_rstop', 'var_random']
    max_value = numpy.max(map(lambda x: numpy.max(data[x]['all']), keys))
    for k in keys:
        val = data[k]['all']
        r.data(k, val).data_rgb('retina', scale(values2retina(val), max_value=max_value))


    keys = ['stop_minus_start', 'rstop_minus_start', 'rstop_minus_stop']
    for k in keys:
        val = data[k]
        r.data(k, val).data_rgb('retina', posneg(values2retina(val)))
        
        
    f = r.figure(shape=(3, 4))
    f.sub('mean_start', 'Mean %s at saccade start' % image_name)
    f.sub('mean_stop', 'Mean %s at saccade stop' % image_name)
    f.sub('mean_rstop', 'Mean %s at random stop' % image_name)
    f.sub('mean_random', 'Mean %s at random direction' % image_name)
    f.sub('var_start', 'Variance %s at saccade start' % image_name)
    f.sub('var_stop', 'Variance %s at saccade stop' % image_name)
    f.sub('var_rstop', 'Variance %s at random stop' % image_name)
    f.sub('var_rstop', 'Variance %s at random direction' % image_name)
    f.sub('stop_minus_start')
    f.sub('rstop_minus_start')
    f.sub('rstop_minus_stop')
    
    
    fall = r.figure('samples', shape=(3,4))
    for id, value in  data['mean_random']['samples'].items():
        r.data_rgb('random-%s' % id, scale(values2retina(value)))
        fall.sub('random-%s' % id)

    return r

def write_report(reports, db, filename):
    output_file = os.path.join(db, filename)    
    r = Report('saccades_view_analysis', children=reports)
    
    print "Writing to %s" % output_file
    r.to_html(output_file)

    
    
        
        
    
    
        
         
