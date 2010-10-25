from flydra.a2 import core_analysis
from flydra_render import logger
import numpy
import scipy.stats

warned_fixed_dt = False

def get_good_smoothed_tracks(filename, obj_ids,
                             min_frames_per_track,
                             use_smoothing,
                             dynamic_model_name):
    ''' Yields (obj_id, rows) for each track in obj_ids in the file
        that has the given minimum number of frames. '''
            
    frames_per_second = 60.0
    dt = 1 / frames_per_second


    ca = core_analysis.get_global_CachingAnalyzer()  
        
    warned = False
    
    #obj_ids, unique_obj_ids, is_mat_file, data_file, extra = \
    #     ca.initial_file_load(filename)
    data_file = filename
    
    for obj_id in obj_ids:
        try:
            frows = ca.load_data(obj_id, data_file, use_kalman_smoothing=False)

            # don't consider tracks too small
            if len(frows) < min_frames_per_track:
                continue

            # write timestamp entry
            
            # The 'timestamp' field returned by flydra is the time
            # when the computation was made, not the actual data timestamp.
            # For computing the actual timestamp, use the frame number
            # and multiply by dt
            
            global warned_fixed_dt
            if not warned_fixed_dt:
                warned_fixed_dt = True
                logger.info('Warning: We are assuming that the data is ' \
                      'equally spaced, and fps = %s.' % frames_per_second)

            for i in range(len(frows)):
                frows['timestamp'][i] = frows['frame'][i] * dt
                
            for i in range(len(frows) - 1):
                if frows['obj_id'][i] == frows['obj_id'][i + 1]:
                    assert frows['timestamp'][i] < frows['timestamp'][i + 1]
                

            # return raw data if smoothing is not requested
            if not use_smoothing:
                yield obj_id, frows
                continue

            # otherwise, run the smoothing
            srows = ca.load_data(obj_id, data_file, use_kalman_smoothing=True,
                     frames_per_second=frames_per_second,
                     dynamic_model_name=dynamic_model_name);
                     
            # make a copy, just in case
            srows = srows.copy()

            for i in range(len(srows)):
                srows['timestamp'][i] = srows['frame'][i] * dt
            
            
            # From Andrew:
            
            # I'm pretty sure there is an inconsistency in some of this 
            # unit stuff. Basically, I used to do the camera calibrations 
            # all in mm (so that the 3D coords would come out in mm). Then,
            # I started doing analyses in meters... And I think some of
            # the calibration and dynamic model stuff got defaulted to meters.
            # And basically there are inconsistencies in there.
            # Anyhow, I think the extent of the issue is that you'll be off 
            # by 1000, so hopefully you can just determine that by looking at the data.

            # quick fix
            if dynamic_model_name == "mamarama, units: mm" and not warned:
                warned = True
                logger.info("Warning: Implementing simple workaround for flydra's " \
                      "units inconsistencies (multiplying xvel,yvel by 1000).")
                
                srows['xvel'] *= 1000
                srows['yvel'] *= 1000
                srows['xvel'] *= 1000

                v = numpy.hypot(srows['xvel'],srows['yvel'],srows['zvel'])
                score95 = scipy.stats.scoreatpercentile(v, 95)
    
      
                if score95 < 100.0:
                    logger.debug( " score95 = %f, assuming m" % score95)
                else:
                    logger.debug( " score95 = %f, assuming mm" % score95)
                    
                    srows['xvel'] *= 0.001
                    srows['yvel'] *= 0.001
                    srows['xvel'] *= 0.001

                v = numpy.hypot(srows['xvel'],srows['yvel'],srows['zvel'])
                final_score95 = scipy.stats.scoreatpercentile(v, 95)
                
                logger.info('After much deliberation, 95% score is %f.' % 
                            final_score95)
                
            yield obj_id, srows 
            
        except core_analysis.NotEnoughDataToSmoothError:
            logger.warning('not enough data to smooth obj_id %d, skipping.'%(obj_id,))
            continue 
        
    ca.close()
