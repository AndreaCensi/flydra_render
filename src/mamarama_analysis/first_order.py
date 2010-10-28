from optparse import OptionParser
import sys, os

from compmake import comp, compmake_console, set_namespace, comp_prefix

from flydra_render.db import FlydraDB
from procgraph_flydra.values2retina import values2retina

from mamarama_analysis import logger

import numpy 
from mamarama_analysis.first_order_intervals import interval_fast, interval_all ,\
    interval_between_saccades, interval_saccades

from reprep import Report  
from reprep.graphics.posneg import posneg
from reprep.graphics.scale import scale
from compmake.jobs.progress import progress
from procgraph.components.statistics.cov2corr import cov2corr 
from mamarama_analysis.covariance import Expectation
from mamarama_analysis.first_order_gui import create_gui


description = """

    samples groups   (all, posts, noposts)
    time interval    (all, fast)
    image            (contrast, contrast_w, ...)
    signal/component (vx,vy,vz,...) (which index: None, 0,1...)
    signal_op        (identity, sign)

"""

# (id, desc, field, component
signal_specs = [
     #   ('vx', 'Forward velocity', 'linear_velocity_body', 0),
     #   ('vy', 'Forward velocity', 'linear_velocity_body', 1),
        ('vz', 'Vertical velocity', 'linear_velocity_body', 2),
        ('avel', 'Angular velocity', 'reduced_angular_velocity', None),
        ('aacc', 'Angular acceleration', 'reduced_angular_acceleration', None)
]


def op_sign(x):
    return numpy.sign(x)

def op_identity(x):
    return x


# (id, desc, function)
signal_op_specs = [
        ('sign', 'Sign', op_sign),
        ('id', 'Raw', op_identity)            
]


# (table, desc) 
image_specs = [
        ('luminance', 'Raw luminance'),
        ('luminance_w', 'Raw luminance (only posts)'),
        ('contrast', 'Contrast'),
        ('contrast_w', 'Contrast (only posts)'),
]

# (id, desc, interval_function)
# interval_function gets as arguments (FlydraDB, sample_id)
# and should return a boolean array, the length of the "rows" table,
# indicating which time instant should be included in the computation.
interval_specs = [
        ('allt', 'All times', interval_all),
        ('fast', 'Fast motion', interval_fast),
        ('saccade', 'Saccades only', interval_saccades),
        ('between', 'Between saccades', interval_between_saccades),
]   

group_specs = [
        ('posts', 'Samples with posts'),
        ('noposts', 'Samples without posts'),
] 


def main():
    
    set_namespace('first_order_new')
    parser = OptionParser()

    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

    (options, args) = parser.parse_args() #@UnusedVariable
    
    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)

    db = FlydraDB(options.db)

    groups = {}
    groups['all'] = set(db.list_samples()) 
    

    groups['posts'] = set(filter(
                      lambda x: db.get_attr(x, 'stimulus', None) != 'nopost',
                      groups['all']))
    groups['noposts'] = set(filter(lambda x: db.get_attr(x, 'stimulus', None) == 'nopost',
                      groups['all']))
    
    all_reports = []
    
    comp(create_gui, '%s/out/first_order/report/' % options.db)
    
    for group_spec in group_specs:
        for interval_spec in interval_specs:
            for signal_spec in signal_specs:
                for signal_op_spec in signal_op_specs:
                    for image_spec in image_specs:
                                                
                        group_id, group_desc = group_spec
                        interval_id, interval_desc, interval_function = interval_spec
                        signal_id, signal_desc, signal, signal_component = signal_spec
                        signal_op_id, signal_op_desc, signal_op_function = signal_op_spec
                        image_id, image_desc = image_spec
                        
                        # Skip uninteresting combinations
                        if image_id.endswith('_w') and group_id == 'noposts':
                            continue
 
                        exp_id = '{image_id}-{signal_id}-{signal_op_id}' \
                                '-{group_id}-{interval_id}' .format(**locals())
                                 
                        description = """
Experiment-ID: {exp_id}

Group: {group_id} --- {group_desc}
Interval: {interval_id} --- {interval_desc}
Signal: {signal_id} --- {signal_desc}
SignalOp: {signal_op_id} --- {signal_desc}
Image: {image_id} --- {image_desc}
""".format(**locals())
                           
                    
                        samples = groups[group_id]
                        
                        comp_prefix(exp_id)
                        
                        data = comp(compute_signal_correlation_unique,
                            db=options.db,
                            interval_function=interval_function,
                            samples=samples,
                            image=image_id,
                            signal=signal,
                            signal_component=signal_component,
                            signal_op=signal_op_function
                        )
                        
                        report = comp(create_report, exp_id, data)
                        
                        comp(write_report, report, options.db, exp_id)

    db.close()

    comp_prefix()
    
    
    compmake_console()
    
     
     
def create_report(exp_id, data):
    r = Report(exp_id) 

    image_mean = data['image_mean']
    image_covariance = data['image_covariance']
    image_variance = image_covariance.diagonal()
    
    r.data_rgb('image_mean', scale(values2retina(image_mean)))
    r.data_rgb('image_var', scale(values2retina(image_variance)))
    a = data['action_image_correlation']
    r.data_rgb('action', posneg(values2retina(a)))
                
    f = r.figure()
    f.sub('action', 'Correlation between action and image')
    f.sub('image_mean', 'Average image')
    f.sub('image_var', 'Variance of image')

    max_corr = numpy.max(numpy.abs(a))
    
    r.table('stats', [[max_corr]], ['max_corr'], 'Some statistics')

    return r


def write_report(report, db, exp_id):
    output_file = os.path.join(db, 'out/first_order/report/%s.html' % exp_id)
    resources = os.path.join(db, 'out/first_order/report/images/')
    report.to_html(output_file, resources)


def compute_signal_correlation_unique(
        db,
        samples,
        interval_function,
        image,
        signal,
        signal_component,
        signal_op
                        ):
    
     
    db = FlydraDB(db)

    image_ex = Expectation()
    actions_ex = Expectation()
    
    # first compute mean
    for sample, actions, image_values in enumerate_data(db, samples, interval_function, 
                                                image, signal, signal_component,
                                                signal_op,  'first pass'):
        
        n = image_values.shape[0]
        # we shouldn't receive empty subsets 
        assert n > 0
        image_ex.update( image_values.mean(axis=0),  n)
        actions_ex.update( actions.mean(axis=0), n)
    
    
    mean_action = actions_ex.get_value()
    mean_image = image_ex.get_value()
    
    assert numpy.isfinite(mean_action).all()
    assert numpy.isfinite(mean_image).all()
    
    cov_z = Expectation()
    
    # do a second pass for computing the covariance    
    for sample, actions, image_values in enumerate_data(db, samples, interval_function, 
                                                image, signal, signal_component,
                                                signal_op, 'second pass'):
        actions = actions - mean_action
        image_values = image_values - mean_image
        # hstack is picky; reshape as column
        actions = actions.reshape((len(actions),1))
        z = numpy.hstack((actions, image_values))
        cov_z.update(numpy.dot(z.T, z)) 
            
    covariance = cov_z.get_value()
    correlation = cov2corr(covariance, zero_diagonal=True)

    image_covariance = covariance[1:,1:]
    image_correlation= correlation[1:,1:]
    action_variance = covariance[0,0]
    action_image_correlation = correlation[0,1:]

    print covariance.dtype
    
    data = {
           'covariance': covariance,
           'correlation': correlation,
           'image_covariance': image_covariance,
           'image_correlation': image_correlation,
           'action_variance': action_variance,
           'action_image_correlation': action_image_correlation,
           'image_mean': mean_image,
           'action_mean': mean_action
    }
    
    db.close()
    
    return data



def enumerate_data(db, samples, interval_function, image, signal, signal_component,
                       signal_op, what='enumerate_data'):
    for k, id in enumerate(samples):
        progress(what, (k, len(samples)), "Sample %s" % id)
        
        
        if not db.has_rows(id):
            logger.warning('Could not find rows table for %s; skipping.' % 
                           (id))
            continue
        
        if not db.has_table(id, image):
            logger.warning('Could not find table "%s" for %s; skipping.' % 
                           (image, id))
            continue
            
        
        rows_table = db.get_rows(id)
        image_table = db.get_table(id, image)
        image_values = image_table[:]['value']
        
        try:
            interval = interval_function(db, id, rows_table) 
        except Exception as e:
            logger.warning('Cannot compute interval for sample %s: %s '\
                           % (id, e))
            continue
        
        if numpy.logical_not(interval).all():
            logger.warning('Sample %s with interval function "%s" gives empty subset;'
                           ' skipping. '%  (id, interval_function.__name__))
            continue
            
        percentage = numpy.mean(interval * 1.0) * 100
        
        #logger.info('Sample %s: function "%s" selects %.1f%% of data.' % 
        #            (id, interval_function.__name__, percentage)) 
        
        # subset everything
        image_values = image_values[interval]
        rows = rows_table[interval]
        
        # get the action vector
        actions = numpy.zeros(shape=(len(rows),), dtype='float32')
        for i in range(len(rows)):
            if signal_component is not None:
                actions[i] = rows[i][signal][signal_component]
            else:
                actions[i] = rows[i][signal]
                
        actions = signal_op(actions)
    
        yield id, actions, image_values

        
        db.release_table(rows_table)
        db.release_table(image_table)
        
        # use only one sample (for debugging)
        # break
        
        
