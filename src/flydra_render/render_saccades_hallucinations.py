import sys, numpy
from optparse import OptionParser

from flydra_render import logger
from flydra_render.db import FlydraDB
from flydra_render.progress import progress_bar
from flydra_render.main_render import get_rfsee_client
from flydra_render.main_render_hallucinations import get_stimulus_to_use
from flydra_render.render_saccades import render_saccades_view

description = """

Usage: ::

    $ flydra_render_saccades --db <flydra db>  [--white] [--nocache] [IDs]

This program iterates over the ``saccades`` table, and renders the scene 
at the beginning and end of the saccade.

Four tables are created:

- ``saccades_view_start_luminance``: view at the beginning of the 
  saccade, given by the field ``orientation_start``.
  
- ``saccades_view_stop_luminance``: view at the end of the saccade, 
  given by the field ``orientation_stop``.
  
- ``saccades_view_rstop_luminance``: view according to data sample 

- ``saccades_view_random_luminance``: view according to random position


  
Each of these tables is as big as the saccades table.

If ``--white`` is specified, the arena walls are displayed in white. 
In this case, the tables are named ``saccades_view_start_luminance_w``,
``saccades_view_stop_luminance_w``

The ``--host`` option allows you to use a remote fsee instance.
See the documentation for ``flydra_render`` for details.

"""

def main():
    
    parser = OptionParser(usage=description)

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
            db.has_table(sample_id, target_random) and \
            not options.nocache:
            logger.info('Targets already computed for %s; skipping' % sample_id)
            continue
        
        # Get the stimulus description
        saccades = db.get_saccades(sample_id)
        
        view_start, view_stop, view_rstop, view_random = render_saccades_view(
            saccades=saccades,
            stimulus_xml=stimulus_xml,
            host=options.host,
            white=options.white)
   
        db.set_table(sample_id, target_start, view_start)
        db.set_table(sample_id, target_stop, view_stop)
        db.set_table(sample_id, target_rstop, view_rstop)
        db.set_table(sample_id, target_random, view_random)
         
    db.close()

if __name__ == '__main__':
    main()
