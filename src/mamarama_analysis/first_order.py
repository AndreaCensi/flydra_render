from optparse import OptionParser
import sys, os, itertools, numpy  

from compmake import comp, compmake_console, set_namespace, comp_prefix
from procgraph.components.statistics.cov2corr import cov2corr # XXX: remove dep
from reprep import Report, posneg, scale

from flydra_db import FlydraDB

from procgraph_flydra.values2retina import values2retina, add_reflines

from . import logger
from .first_order_intervals import interval_fast, interval_all , \
    interval_between_saccades, interval_saccades
from .covariance import Expectation
from .first_order_gui import create_gui
from .first_order_timecorr import create_report_delayed

from .first_order_commands import compute_general_statistics
from .first_order_data import enumerate_data
from .saccades_view_joint_analysis import add_posneg


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
        ('avel', 'Angular velocity', 'reduced_angular_velocity', None),
        ('aacc', 'Angular acceleration', 'reduced_angular_acceleration', None),
        
        #('vx', 'Forward velocity', 'linear_velocity_body', 0),
        ('vz', 'Vertical velocity', 'linear_velocity_body', 2),
        ('az', 'Vertical acceleration', 'linear_acceleration_body', 2),
]


def op_sign(x):
    return numpy.sign(x)

def op_identity(x):
    return x


# (id, desc, function)
signal_op_specs = [
        ('id', 'Raw', op_identity),
        ('sign', 'Sign', op_sign),
]


# (table, desc) 
image_specs = [
        ('luminance', 'Raw luminance'),
        ('luminance_w', 'Raw luminance (only posts)'),
        ('contrast', 'Contrast'),        
        ('contrast_w', 'Contrast (only posts)'),
        ('hcontrast', 'Hallucinated Contrast'),
        ('hcontrast_w', 'Hallucinated Contrast (only posts)'),
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
    groups['noposts'] = set(filter(lambda x: db.get_attr(x, 'stimulus', None) 
                                   == 'nopost',
                      groups['all']))
    
    all_experiments = {}
    
    comp(create_gui, '%s/out/first_order/report/' % options.db)
     
    for group_spec, interval_spec, signal_spec, signal_op_spec, image_spec \
        in itertools.product(group_specs, interval_specs, signal_specs,
                             signal_op_specs, image_specs):
                                                
        group_id, group_desc = group_spec       
        
        interval_id, interval_desc, interval_function = interval_spec
        signal_id, signal_desc, signal, signal_component \
 = signal_spec
        signal_op_id, signal_op_desc, signal_op_function \
 = signal_op_spec
        image_id, image_desc = image_spec
        
        # Skip uninteresting combinations
        is_hallucination = image_id.startswith('h')
        white_arena = image_id.endswith('_w') 
        
        if (not is_hallucination) and white_arena and (group_id == 'noposts'):
            # if there are not posts, it's useless 
            continue
        
        if is_hallucination  and (group_id == 'posts'):
            # we only hallucinate the ones without posts
            continue
        
        # find the sample which have the image
        samples = filter(lambda x: db.has_table(x, image_id), groups[group_id])
        
        if not samples:
            raise Exception('No samples for %s/%s' % (group_id, image_id))
        
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
            
        
        comp_prefix(exp_id)
        
        data = comp(compute_signal_correlation_unique,
            db=options.db,
            interval_function=interval_function,
            samples=samples,
            image=image_id,
            signal=signal,
            signal_component=signal_component,
            signal_op=signal_op_function,
            delay=0
        )
        
        report = comp(create_report, exp_id, data, description=description)
                
        
        comp(write_report, report, options.db, exp_id)
        
        
        delayed = {}
        delays = range(-5, 11)
        for delay in delays:
            job_id = 'timecorr%d' % delay
            delayed[delay] = comp(compute_signal_correlation_unique,
                db=options.db,
                interval_function=interval_function,
                samples=samples,
                image=image_id,
                signal=signal,
                signal_component=signal_component,
                signal_op=signal_op_function,
                delay=delay,
                job_id=job_id)
        report_delayed = comp(create_report_delayed, exp_id + '_delayed', delayed,
                description)
        comp(write_report, report_delayed, options.db, exp_id + '_delayed')
        
        all_experiments[exp_id] = delayed    

    # Compute general statistics 
    for group_spec, interval_spec, signal_spec  \
        in itertools.product(group_specs, interval_specs, signal_specs):

        group_id, group_desc = group_spec
        samples = groups[group_id]
                
        interval_id, interval_desc, interval_function = interval_spec
        signal_id, signal_desc, signal, signal_component = signal_spec
                
        data_id = '{signal_id}-{group_id}-{interval_id}' .format(**locals())
        
        comp_prefix(data_id)
        
        report = comp(compute_general_statistics,
            id=data_id,
             db=options.db,
             samples=samples,
             interval_function=interval_function,
             signal=signal, signal_component=signal_component)
    
        comp(write_report, report, options.db, data_id)

    db.close()

    comp_prefix()

    # now some very specific processing
    
    real = all_experiments['contrast_w-avel-id-posts-between'][5]
    hall = all_experiments['hcontrast_w-avel-id-noposts-between'][5]
    outdir = os.path.join(options.db, 'out/first_order_special')
    page_id = 'contrast_w-avel'
    comp(compare, real, hall, outdir, page_id)
    
    
    compmake_console()
    
def normalize_diff(a,b):
    diff = a - b
    
    pos = numpy.nonzero(a > 0)
    diff[pos] = numpy.maximum(0, diff[pos])
    neg = numpy.nonzero(a < 0)
    diff[neg] = numpy.minimum(0, diff[neg])

    return diff

def compare(real_delayed, hall_delayed, outdir, page_id):
    
    r = Report(page_id)
    
    if False:
        delay = 5
        real = real_delayed[delay]
        hall = hall_delayed[delay]
    else:
        real = real_delayed
        hall = hall_delayed
    
    print real.keys()
    
    real_a = real['action_image_correlation']
    hall_a = hall['action_image_correlation'] 
    
    real_ac = real['covariance'][0,1:]
    hall_ac = hall['covariance'][0,1:]
    
    diff = real_a - hall_a
    diffc = real_ac - hall_ac
    
    # find where it differs significantly
    diffn =normalize_diff(real_a, hall_a)
    diffcn =normalize_diff(real_ac, hall_ac)
    
    add_posneg(r, 'real', real_a)
    add_posneg(r, 'hall', hall_a)     
    add_posneg(r, 'realc', real_ac)
    add_posneg(r, 'hallc', hall_ac)
    add_posneg(r, 'diff', diff)
    add_posneg(r, 'diffn', diffn)        
    add_posneg(r, 'diffc', diffc)
    add_posneg(r, 'diffcn', diffcn)
    
    with r.data_pylab('cmp') as pylab:
        pylab.plot(real_a, hall_a, '.')
        pylab.xlabel('real')
        pylab.ylabel('hall')
        pylab.axis('equal')

    with r.data_pylab('correlations') as pylab:
        pylab.plot(real_a, 'b.')
        pylab.plot(hall_a, 'r.')

    
    with r.data_pylab('covariances') as pylab:
        pylab.plot(real_ac, 'b.')
        pylab.plot(hall_ac, 'r.')

#    with r.data_pylab('covariance') as pylab:
#        pylab.plot(numpy.diagonal(real['covariance'], 'b.')

    f= r.figure(shape=(3,2))
    f.sub('real', caption='Real (corr)')
    f.sub('hall', caption='Hallucination (corr) ')
    
    f.sub('realc', caption='Real (cov)')
    f.sub('hallc', caption='Hallucination (cov)')
    
    f.sub('cmp', caption='on the same axis')
    f.sub('cmp', caption='on the same axis')
    
    f.sub('diff', caption='difference (real-hall) ')
    f.sub('diffn', caption='difference (real-hall) clipped')

    f.sub('diffc', caption='difference (real-hall) ')
    f.sub('diffcn', caption='difference (real-hall) clipped')
    
    f.sub('correlations')
    f.sub('covariances')
    
    filename = os.path.join(outdir, page_id+'.html')
    resources = os.path.join(outdir, 'images')
    print "Writing to %s" % filename
    r.to_html(filename, resources)
     
     
     
def create_report(exp_id, data, description):
    r = Report(exp_id) 
    r.text('description', description)

    image_mean = data['image_mean']
    image_covariance = data['image_covariance']
    image_variance = image_covariance.diagonal()
    
    r.data_rgb('image_mean', add_reflines(scale(values2retina(image_mean), min_value=0)))
    r.data_rgb('image_var', add_reflines(scale(values2retina(image_variance), min_value=0)))
    a = data['action_image_correlation']
    r.data_rgb('action', add_reflines(posneg(values2retina(a))))
                
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
        signal_op,
        delay=0
                        ):
    
     
    db = FlydraDB(db, False)

    image_ex = Expectation()
    actions_ex = Expectation()
    
    # first compute mean
    iter =  enumerate_data(db, samples, interval_function, 
                           image, signal, signal_component,
                           signal_op, 'first pass')
        
    for sample, actions, image_values in iter: #@UnusedVariable
        n = image_values.shape[0]
        # we shouldn't receive empty subsets 
        assert n > 0
        image_ex.update(image_values.mean(axis=0), n)
        actions_ex.update(actions.mean(axis=0), n)
    
    
    mean_action = actions_ex.get_value()
    mean_image = image_ex.get_value()

    print mean_action.shape, mean_action.dtype    
    assert numpy.isfinite(mean_action).all()
    assert numpy.isfinite(mean_image).all()
    
    cov_z = Expectation()
    
    # do a second pass for computing the covariance
    iter = enumerate_data(db, samples, interval_function,
                          image, signal, signal_component,
                          signal_op, 'second pass')    
    for sample, actions, image_values in iter: #@UnusedVariable
        # do not remove the mean (should be 0)
        # actions = actions - mean_action
        image_values = image_values - mean_image
        # hstack is picky; reshape as column
        actions = actions.reshape((len(actions), 1))
        
        if delay > 0:
            actions = actions[delay:, :]
            image_values = image_values[:-delay, :]
        elif delay < 0:
            d = -delay
            image_values = image_values[d:, :]
            actions = actions[:-d, :]
        else:
            # we are all good
            pass
        
        
        z = numpy.hstack((actions, image_values))
        cov_z.update(numpy.dot(z.T, z)) 
            
    covariance = cov_z.get_value()
    correlation = cov2corr(covariance, zero_diagonal=True)

    image_covariance = covariance[1:, 1:]
    image_correlation = correlation[1:, 1:]
    action_variance = covariance[0, 0]
    action_image_correlation = correlation[0, 1:]
 
    data = {
           'covariance': covariance,
           'correlation': correlation,
           'image_covariance': image_covariance,
           'image_correlation': image_correlation,
           'action_variance': action_variance,
           'action_image_correlation': action_image_correlation,
           'image_mean': mean_image,
           'action_mean': mean_action,
           'delay': delay,
    }
    
    db.close()
    
    return data


