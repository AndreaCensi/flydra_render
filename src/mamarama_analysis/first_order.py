from optparse import OptionParser
import sys, os

from compmake import comp, compmake_console, comp_prefix, set_namespace
from reprep import Report

from flydra_render.db import FlydraDB
from procgraph_flydra.values2retina import values2retina

from mamarama_analysis import logger
from mamarama_analysis.covariance import compute_image_mean



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
    groups['posts'] = set(filter(lambda x: db.get_attr(x, 'stimulus', None) != 'nopost',
                                  groups['all']))
    groups['noposts'] = set(filter(lambda x: db.get_attr(x, 'stimulus', None) == 'nopost',
                                groups['all']))
    
    
    groups['posts+contrast'] = groups['posts'].intersection(groups['has_contrast'])
    groups['noposts+contrast'] = groups['noposts'].intersection(groups['has_contrast'])
    
    
    all_reports = []
    
    use_groups = ['posts+contrast', 'noposts+contrast']
    
    set_namespace('first_order')
    for group_name in use_groups:
        samples = groups[group_name]
        print 'group %s: %s' % (group_name, samples)        
        
        comp_prefix(group_name)
        
        data = {}
        data['mean_luminance'] = comp(compute_image_mean, options.db, samples, 'luminance',
                                      job_id='mean_luminance')
        data['mean_contrast'] = comp(compute_image_mean, options.db, samples, 'contrast',
                                     job_id='mean_contrast')
        
        report = comp(create_report, group_name, data)
        all_reports.append(report)
        
    comp_prefix()

    comp(write_report, all_reports, options.db)
    compmake_console()
        
def create_report(group_name, data):
    r = Report(group_name)
    f = r.figure('means')
    
    for m in ['mean_luminance', 'mean_contrast']:
        x = data[m]
        with r.data_pylab(m) as pylab:
            pylab.imshow(values2retina(x))
            
        f.sub(m)
        
    return r

def write_report(reports, db):
    output_file = os.path.join(db, 'out/first_order/report/index.html')
    r = Report('first_order', children=reports)
    r.to_html(output_file)
    
    
    
        
        
    
    
        
         
