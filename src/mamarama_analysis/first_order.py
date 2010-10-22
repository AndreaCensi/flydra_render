from optparse import OptionParser
import sys, os

from compmake import comp, compmake_console, set_namespace, comp_prefix

from flydra_render.db import FlydraDB
from procgraph_flydra.values2retina import values2retina

from mamarama_analysis import logger

import numpy 
from mamarama_analysis.first_order_intervals import interval_fast, interval_all
from mamarama_analysis.actions import compute_signal_correlation

from reprep import Report  
from reprep.graphics.posneg import posneg
from reprep.graphics.scale import scale


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
        ('vz', 'Forward velocity', 'linear_velocity_body', 2),
        ('avel', 'Angular velocity', 'reduced_angular_velocity', None),
        ('aacc', 'Angular acceleration', 'reduced_angular_acceleration', None)
]

# (id, desc, function)

def op_sign(x):
    return numpy.sign(x)
def op_identity(x):
    return x

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
                        
                        data = comp(compute_signal_correlation,
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

    comp_prefix()
    
    compmake_console()
    
#    
#def normalization(field, cov):
#    #return numpy.linalg.solve(cov, field)
#    return numpy.dot(numpy.linalg.pinv(cov), field)

def create_report(exp_id, data):
    r = Report(exp_id)
    
    C = data['correlation']
    
    action = C[0, 1:]
    image_mean = data['image_mean']
    
    r.data('action', action).data_rgb('posneg', posneg(values2retina(action)))
    r.data('image_mean', image_mean).data_rgb('scale', scale(values2retina(image_mean)))
                
    f = r.figure()
    f.sub('action')
    f.sub('image_mean')

    return r

def write_report(report, db, exp_id):
    output_file = os.path.join(db, 'out/first_order/reports/%s.html' % exp_id)
    report.to_html(output_file)

    
        
