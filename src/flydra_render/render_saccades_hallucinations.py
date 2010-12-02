from optparse import OptionParser

from flydra_db import FlydraDB

from . import logger
from .main_render_hallucinations import get_stimulus_to_use
from .render_saccades import render_saccades_view
 
def main():
    
    parser = OptionParser()

    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

    parser.add_option("--nocache", help="Ignores already computed results.",
                      default=False, action="store_true")
    
    parser.add_option("--white", help="Computes luminance_w, with the arena"
                      " painted white.", default=False, action="store_true")
    
    parser.add_option("--host", help="Use a remote rfsee. Otherwise," 
                      "use local process.", default=None)
    
    (options, args) = parser.parse_args()
     
    db = FlydraDB(options.db, False)
    
    if args:
        do_samples = args
        
    else:
        # look for samples with the rows table
        all_samples = db.list_samples()
        do_samples = filter(lambda x: db.has_saccades(x) and 
                                      db.has_attr(x, 'stimulus') and
                                      db.get_attr(x, 'stimulus') == 'nopost',
                            all_samples)
        logger.info('Found %d/%d samples with saccades and stimulus nopost.' % 
                    (len(do_samples), len(all_samples)))
    
    stimulus_to_use = list(get_stimulus_to_use(db, len(do_samples)))

    image = 'hluminance_w' if options.white else 'hluminance'
        
    target_start = 'saccades_view_start_%s' % image
    target_stop = 'saccades_view_stop_%s' % image
    target_rstop = 'saccades_view_rstop_%s' % image
    target_sstop = 'saccades_view_sstop_%s' % image
    target_random = 'saccades_view_random_%s' % image
    
    for i, sample_id in enumerate(do_samples):
        
        stimulus = stimulus_to_use[i][0]
        stimulus_xml = stimulus_to_use[i][1]
        
        logger.info('Sample %s/%s: %s, previously %s now %s' % 
                    (i + 1, len(do_samples), sample_id,
                     db.get_attr(sample_id, 'stimulus'), stimulus))
        
        if not db.has_sample(sample_id):
            raise Exception('Sample %s not found in db.' % sample_id)
        
        if not db.has_saccades(sample_id):
            raise Exception('Sample %s does not have saccades table.' % sample_id)
               
        # todo: check stale dependencies
        if db.has_table(sample_id, target_start) and \
            db.has_table(sample_id, target_stop) and \
            db.has_table(sample_id, target_rstop) and \
            db.has_table(sample_id, target_sstop) and \
            db.has_table(sample_id, target_random) and \
            not options.nocache:
            logger.info('Targets already computed for %s; skipping' % sample_id)
            continue
        
        # Get the stimulus description
        saccades = db.get_saccades(sample_id)
        
        view_start, view_stop, view_rstop, view_random, view_sstop = \
            render_saccades_view(
                saccades=saccades,
                stimulus_xml=stimulus_xml,
                host=options.host,
                white=options.white)
   
        db.set_table(sample_id, target_start, view_start)
        db.set_table(sample_id, target_stop, view_stop)
        db.set_table(sample_id, target_rstop, view_rstop)
        db.set_table(sample_id, target_sstop, view_sstop)
        db.set_table(sample_id, target_random, view_random)
        
        db.release_table(saccades)
        
    db.close()

if __name__ == '__main__':
    main()
