from . import logger
from ..utils import (LenientOptionParser, UserError, get_user,
    wrap_script_entry_point)
from .flydra_db_utils import get_good_smoothed_tracks
from .main_filter_meat import filter_rows
from StringIO import StringIO
from datetime import datetime
from flydra_db import FlydraDB
from geometric_saccade_detector.flydra_db_utils import get_good_files
import os
import numpy
import sys
import platform


def main_filter(args):
    parser = LenientOptionParser()
    
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

    
    (options, args) = parser.parse_args(args)
    
    table_name = 'rows' # TODO: use constant
    table_version = "smooth" if options.smoothing else "kf"
    
    
    if not args:
        raise UserError('No files or directories specified.')
         
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
        
            
        logger.info("File %d/%d %s %s %s " % 
                    (i, n, str(filename), str(obj_ids), stim_fname))
       
        if (db.has_sample(sample_id) 
            and db.has_table(sample_id, table_name, table_version)
            and not options.nocache):
            logger.info('Sample %r already computed; skipping.'
                        ' (use --nocache to ignore)' % sample_id)
            continue
  
        all_data = [] 

        for obj_id, rows in get_good_smoothed_tracks(#@UnusedVariable
                filename=filename,
                obj_ids=obj_ids,
                min_frames_per_track=options.min_frames_per_track,
                dynamic_model_name=options.dynamic_model_name,
                use_smoothing=options.smoothing):

            filtered = filter_rows(rows, options)
            all_data.append(filtered)
             
        if not all_data:
            logger.info('Not enough data found for %r; skipping.' % sample_id)
            continue

  
        if not db.has_sample(sample_id):
            db.add_sample(sample_id)
        db.set_attr(sample_id, 'stim_fname', stim_fname)
        db.set_attr(sample_id, 'stimulus', stim)
        stim_xml = open(stim_fname).read()
        db.set_attr(sample_id, 'stimulus_xml', stim_xml)
        
        geometry = get_posts_info(stim_xml)
        print(geometry)
        db.set_attr(sample_id, 'posts', geometry['posts'])
        if 'arena' in geometry:
            db.set_attr(sample_id, 'arena', geometry['arena'])


        db.add_sample_to_group(sample_id, stim)
        if stim != 'nopost':
            db.add_sample_to_group(sample_id, 'posts')
            

        rows = numpy.concatenate(all_data)
        db.set_table(sample=sample_id,
                     table=table_name,
                     data=rows,
                     version=table_version)
    
        
        db.set_attr(sample_id, 'filter_time', datetime.now().strftime("%Y%m%d_%H%M%S"))
        db.set_attr(sample_id, 'filter_host', platform.node())
        db.set_attr(sample_id, 'filter_user', get_user())
        db.set_attr(sample_id, 'filter_python_version', platform.python_version())
        db.set_attr(sample_id, 'filter_numpy_version', numpy.version.version)
        
         
    db.close()
    

    

def get_posts_info(xml):
    from flydra.a2 import xml_stimulus #@UnresolvedImport
    stimulus_xml = StringIO(xml)
    stim_xml = xml_stimulus.xml_stimulus_from_filename(stimulus_xml)
    root = stim_xml.get_root()
    
    results = {'posts':[]}
    for child in root:
        if child.tag == 'cylindrical_post':
            info = stim_xml._get_info_for_cylindrical_post(child)
            results['posts'].append(info)
        elif child.tag == 'cylindrical_arena':
            results['arena'] = stim_xml._get_info_for_cylindrical_arena(child)

    return results
          


def main():
    wrap_script_entry_point(main_filter, logger)
    
if __name__ == '__main__':
    main()
    
