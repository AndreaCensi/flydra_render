#!/usr/bin/env python
import  os, numpy, sys, platform, pwd 
from optparse import OptionParser
from datetime import datetime

# TODO: remove 
from geometric_saccade_detector.flydra_db_utils import get_good_files
from flydra_db import FlydraDB

from . import logger
from .main_filter_meat import filter_rows
from .flydra_db_utils import get_good_smoothed_tracks


def main():
    parser = OptionParser()
    
    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

    parser.add_option("--min_frames_per_track", default=400,
        help="Minimum number of frames per track [= %default]")

    parser.add_option("--confirm_problems",
                      help="Stop interactively on problems with log files'\
                      '(e.g.: cannot find valid obj_ids) [default: %default]",
                      default=False, action="store_true")

    parser.add_option("--dynamic_model_name",
                      help="Smoothing dynamical model [default: %default]",
                      default="mamarama, units: mm")
    
    parser.add_option("--debug_output", help="Creates debug figures.",
                      default=False, action="store_true")

    parser.add_option("--nocache", help="Ignores already computed results.",
                      default=False, action="store_true")

    parser.add_option("--smoothing", help="Uses Kalman-smoothed data.",
                      default=False, action="store_true")

    
    (options, args) = parser.parse_args()
    
    if not args:
        logger.error('No files or directories specified.')
        sys.exit(-1)
         
    if not os.path.exists(options.db):
        os.makedirs(options.db)

    db = FlydraDB(options.db)

    good_files = get_good_files(where=args, pattern="*.kh5",
                                confirm_problems=options.confirm_problems)

    if len(good_files) == 0:
        logger.error("No good files to process")
        sys.exit(1)

    n = len(good_files)
    for i in range(n):
        (filename, obj_ids, stim_fname) = good_files[i]
        
        logger.info('Sample %s/%s: %s' % (i + 1, n, filename))
        
        
        # only maintain basename
        stim = os.path.splitext(os.path.basename(stim_fname))[0]
        sample_id = os.path.splitext(os.path.basename(filename))[0]
        
        logger.info("File %d/%d %s %s %s " % (i, n, str(filename), str(obj_ids), stim_fname))
       
        if db.has_sample(sample_id) and \
           db.has_rows(sample_id) and not options.nocache:
            logger.info('Sample %s already computed; skipping. (use --nocache to ignore)' % \
                             sample_id)
            continue
        
        
  
        all_data = [] 

        for obj_id, rows in get_good_smoothed_tracks( #@UnusedVariable
                filename=filename,
                obj_ids=obj_ids,
                min_frames_per_track=options.min_frames_per_track,
                dynamic_model_name=options.dynamic_model_name,
                use_smoothing=options.smoothing):

            filtered = filter_rows(rows, options)
            all_data.append(filtered)
             
        if not all_data:
            logger.info('Not enough data found for %s; skipping.' % filename)
            continue

        if not db.has_sample(sample_id):
            db.add_sample(sample_id)

        rows = numpy.concatenate(all_data)
        db.set_rows(sample_id, rows)
    
        db.set_attr(sample_id, 'stim_fname', stim_fname)
        db.set_attr(sample_id, 'stimulus', stim)
        db.set_attr(sample_id, 'stimulus_xml', open(stim_fname).read())


        db.set_attr(sample_id, 'filter_time', datetime.now().strftime("%Y%m%d_%H%M%S"))
        db.set_attr(sample_id, 'filter_host', platform.node())
        db.set_attr(sample_id, 'filter_user', get_user())
        db.set_attr(sample_id, 'filter_python_version', platform.python_version())
        db.set_attr(sample_id, 'filter_numpy_version', numpy.version.version)
         
    db.close()
    sys.exit(0)



def get_user():    
    try:
        return pwd.getpwuid(os.getuid())[0]
    except:
        return '<unknown user>'


if __name__ == '__main__':
    main()
