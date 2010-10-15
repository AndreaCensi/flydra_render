from optparse import OptionParser
import sys, os

from compmake import comp, compmake_console, comp_prefix, set_namespace
from reprep import Report

from flydra_render.db import FlydraDB
from procgraph_flydra.values2retina import values2retina

from mamarama_analysis import logger
from mamarama_analysis.covariance import compute_image_mean, compute_image_cov
from mamarama_analysis.actions import compute_presaccade_action
import numpy



def main():
    parser = OptionParser()

    parser.add_option("--db", default='flydra_render_output',
                      help="Data directory")

    (options, args) = parser.parse_args() #@UnusedVariable
    
    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)

    db = FlydraDB(options.db)

    groups = {}
    groups['all'] = set(db.list_samples()) 
    groups['has_rows'] = set(filter(lambda x: db.has_rows(x), groups['all']))
    groups['has_contrast'] = set(filter(lambda x: 
                                        db.has_image(x, 'contrast') and
                                        db.has_image(x, 'luminance'),
                                    groups['all']))
    groups['has_saccades'] = set(filter(lambda x: db.has_saccades(x), groups['all']))
    groups['posts'] = set(filter(lambda x: db.get_attr(x, 'stimulus', None) != 'nopost',
                                  groups['all']))
    groups['noposts'] = set(filter(lambda x: db.get_attr(x, 'stimulus', None) == 'nopost',
                                groups['all']))
    
    
    groups['posts+contrast'] = groups['posts']. \
            intersection(groups['has_contrast']).\
            intersection(groups['has_saccades'])
    groups['noposts+contrast'] = groups['noposts'].\
            intersection(groups['has_contrast']).\
            intersection(groups['has_saccades'])
    
    all_reports = []
    
    use_groups = ['posts+contrast', 'noposts+contrast']
    
    set_namespace('first_order')
    for group_name in use_groups:
        samples = groups[group_name]
        
        # only a representation
#        if len(samples) > 5:
#            samples = list(samples)[0:5]
        
        print 'group %s: %s' % (group_name, samples)        
        
        comp_prefix(group_name)
        
        data = {}
        for i in ['luminance', 'contrast']:
            mean = comp(compute_image_mean, options.db,
                        samples, i, job_id='mean_%s' % i)
            cov = comp(compute_image_cov, options.db,
                        samples, i, job_id='cov_%s' % i)
            action_id = comp(compute_presaccade_action, options.db,
                                      samples, i, False, job_id='%s_action_id' % i)
            action_sign = comp(compute_presaccade_action, options.db,
                              samples, i, True, job_id='%s_action_sign' % i)

            action_id_norm = comp(normalization, action_id, cov)
            action_sign_norm = comp(normalization, action_sign, cov)
            
            data['mean_%s' % i] = mean 
            data['cov_%s' % i ] = cov
        
            data['%s_action_id' % i] = action_id 
            data['%s_action_sign' % i] = action_sign
            
            
            data['%s_action_sign_norm' % i] = action_sign_norm
            data['%s_action_id_norm' % i] = action_id_norm
             
        report = comp(create_report, group_name, data)
        all_reports.append(report)
        
    comp_prefix()

    comp(write_report, all_reports, options.db)
    compmake_console()
    
    
def normalization(field, cov):
    #return numpy.linalg.solve(cov, field)
    return numpy.dot(numpy.linalg.pinv(cov), field)

def create_report(group_name, data):
    r = Report(group_name)
    
    
    for m in ['luminance', 'contrast']:
    
        rm = r.node('%s_statistics' % m)
        
        f = rm.figure('%s statistics' % m, shape=(3, 3))
            
        mean = data['mean_%s' % m]
        cov = data['cov_%s' % m]
        
        with rm.data_pylab('mean') as pylab:
            pylab.imshow(values2retina(mean))
        
        with rm.data_pylab('var') as pylab:
            pylab.imshow(values2retina(cov.diagonal()))
        
        with rm.data_pylab('cov') as pylab:
            pylab.imshow(cov)
        
            
        f.sub('mean', '%s mean' % m)
        f.sub('var', '%s variance' % m)
        f.sub('cov', '%s covariance' % m)
        
        action_sign = data['%s_action_sign' % m]
        action_id = data['%s_action_id' % m]
        action_sign_n = data['%s_action_sign_norm' % m]
        action_id_n = data['%s_action_id_norm' % m]
        
        with rm.data_pylab('action_sign') as pylab:
            pylab.imshow(values2retina(action_sign))
        with rm.data_pylab('action_sign_norm') as pylab:
            pylab.imshow(values2retina(action_sign_n))
        
        with rm.data_pylab('action_id') as pylab:
            pylab.imshow(values2retina(action_id))
        with rm.data_pylab('action_id_norm') as pylab:
            pylab.imshow(values2retina(action_id_n))
        
        f.sub('action_id', 'E{%s * action}' % m)
        f.sub('action_id_norm', 'E{%s * action} / cov' % m)
        f.sub('action_sign', 'E{%s * sign(action)}' % m)
        f.sub('action_sign_norm', 'E{%s * sign(action)} / cov' % m)
        
        
    return r

def write_report(reports, db):
    output_file = os.path.join(db, 'out/first_order/report/index.html')
    r = Report('first_order', children=reports)
    r.to_html(output_file)
    
    
    
        
        
    
    
        
         
