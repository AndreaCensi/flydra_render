import sys     
from optparse import OptionParser

from compmake import comp, compmake_console, comp_prefix, set_namespace, \
    batch_command
from reprep import Report

from flydra_db import FlydraDB

from procgraph_flydra.values2retina import  plot_luminance

from mamarama_analysis import logger
from compmake.jobs.syntax.parsing import parse_job_list

description = """

    This program writes a report for each sampling
    displaying the image at start and stop of each saccade.  

"""

def main():
    parser = OptionParser()

    parser.add_option("--db", default='flydra_db', help="Data directory")

    parser.add_option("--image", default="luminance",
                      help="Rendered image to use -- "
            " corresponding to image 'saccades_view_{start,stop}_X'")
    
    parser.add_option("--interactive",
                      help="Start an interactive compmake session."
                      " Otherwise run in batch mode. ",
                      default=False, action="store_true")


    (options, args) = parser.parse_args() #@UnusedVariable
    
    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)

    view_start = 'saccades_view_start_%s' % options.image
    view_stop = 'saccades_view_stop_%s' % options.image
    view_rstop = 'saccades_view_rstop_%s' % options.image    

    db = FlydraDB(options.db, False) 
    
    # all samples with enough data
    all_available = lambda x: db.has_saccades(x) and \
        db.has_table(x, view_start) and \
        db.has_table(x, view_stop) and \
        db.has_table(x, view_rstop)
        
    samples = filter(all_available, db.list_samples())
    
    set_namespace('saccade_view_show_%s' % options.image)
    
    for sample in samples: 
        comp_prefix(sample)
        
        comp(create_and_write_report, options.db, sample, options.image) 
        
    
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
 
    

def create_and_write_report(flydra_db, sample, image_name):
    
    view_start = 'saccades_view_start_%s' % image_name
    view_stop = 'saccades_view_stop_%s' % image_name
    view_rstop = 'saccades_view_rstop_%s' % image_name    


    db = FlydraDB(flydra_db, False) 
    
    saccades = db.get_saccades(sample)
    values_start = db.get_table(sample, view_start)
    values_stop = db.get_table(sample, view_stop)
    values_rstop = db.get_table(sample, view_rstop)
    
    
    r = Report(sample)
    
    for i in range(len(saccades)):
        
        ri = r.node("saccade-%04d" % i)
        
        ri.data_rgb('start', plot_luminance(values_start[i]['value']))
        ri.data_rgb('stop', plot_luminance(values_stop[i]['value']))
        ri.data_rgb('rstop', plot_luminance(values_rstop[i]['value']))
        
        f = ri.figure(shape=(1, 3))
        f.sub('start', 'At saccade start')
        f.sub('stop', 'At saccade stop')
        #f.sub('rstop', '(random stop)')


    db.release_table(saccades)
    db.release_table(values_start)
    db.release_table(values_stop)
    db.release_table(values_rstop)
    

    filename = "%s/out/saccade_view_show/%s_%s.html" % (flydra_db, image_name, sample)
    print "Writing to %s" % filename
    r.to_html(filename)
    
    
        
        
    
    
        
         

