#!/usr/bin/env python
import pickle, os, scipy.io, numpy, sys, platform, tables
from datetime import datetime
from optparse import OptionParser 
from flydra_render import logger
from geometric_saccade_detector.flydra_db_utils import get_good_files, \
    get_good_smoothed_tracks
from rfsee.rfsee_client import ClientTCP



def main():
    parser = OptionParser()

    parser.add_option("--output_dir", default='flydra_render_output',
                      help="Output directory")

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
        
    # Create processed string
#    processed = 'geometric_saccade_detector %s %s %s@%s Python %s' % \
#                (version, datetime.now().strftime("%Y%m%d_%H%M%S"),
#                 get_user(), platform.node(), platform.python_version())
#        

    if not os.path.exists(options.output_dir):
        os.makedirs(options.output_dir)


    good_files = get_good_files(where=args, pattern="*.kh5",
                                confirm_problems=options.confirm_problems)

    if len(good_files) == 0:
        logger.error("No good files to process")
        sys.exit(1)

    n = len(good_files)
    for i in range(n):
        (filename, obj_ids, stim_fname) = good_files[i]
        # only maintain basename
        stim = os.path.splitext(os.path.basename(stim_fname))[0]
        basename = os.path.splitext(os.path.basename(filename))[0]
        
        output_rows = os.path.join(options.output_dir, basename + '.h5')        
        output_luminance = os.path.join(options.output_dir, basename + '-luminance.h5')        
            
        if os.path.exists(output_luminance) and not options.nocache:
            logger.info('File %s exists; skipping. (use --nocache to ignore)' % \
                             output_luminance)
            continue
        
        logger.info("File %d/%d %s %s %s " % (i, n, str(filename), str(obj_ids), stim_fname))
        
        # create the main file with the standard structure
        rows_file = tables.openFile(output_rows, 'w')
        flydra_render_group = rows_file.createGroup('/', 'flydra_render',
                             'base group for flydra_render output')
        samples = rows_file.createGroup(flydra_render_group, 'samples')
        sample = rows_file.createGroup(samples, basename)
        rows_table = None 

        for obj_id, rows in get_good_smoothed_tracks(
                filename=filename,
                obj_ids=obj_ids,
                min_frames_per_track=options.min_frames_per_track,
                dynamic_model_name=options.dynamic_model_name,
                use_smoothing=options.smoothing):

            filtered = filter_rows(rows)
            
            # create table after we have the first data
            if rows_table is None:
                rows_table = rows_file.createTable(sample, 'rows', filtered)
            else:
                rows_table.append(filtered)

        
        if rows_table is None:
            logger.info('Not enough data found for %s; skipping.' % filename)
            continue

        else:
            pass
        
        # now we create the other file
        luminance_file = tables.openFile(output_luminance, 'w')
        flydra_render_group = rows_file.createGroup('/', 'flydra_render',
                             'base group for flydra_render output')
        samples = rows_file.createGroup(flydra_render_group, 'samples')
        sample = rows_file.createGroup(samples, basename)
        render = rows_file.createGroup(samples, 'render')
        
        num_frames = len(rows_table)
        dtype = [ ('obj_id', 'int'),
                 ('frame', 'int'),
                 ('value', ('int', 1398))]
        luminance = numpy.zeros(shape=(num_frames,), dtype=dtype)
        
        cp = ClientTCP(host='tokyo', port=10781)

        cp.config_stimulus_xml(stim_fname)


        for frame in range(num_frames):
        
        


position = [0.5, 0.5, 0.5]
attitude = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
linear_velocity_body = [0, 0, 0]
angular_velocity_body = [0, 0, 0]

res = cp.render(position, attitude, linear_velocity_body, angular_velocity_body)

print res.keys()
print res['luminance']

        # add the data to the file
        rows_file.createTable(render, 'luminance', luminance)
        

        

    sys.exit(0)



def filter_rows(rows):
    return rows


if __name__ == '__main__':
    main()
