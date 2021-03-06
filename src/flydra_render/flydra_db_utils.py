import numpy, os, scipy.stats

from flydra.a2 import core_analysis, xml_stimulus
from flydra_db.db_index import locate_roots

from . import logger

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
        
    #warned = False
    
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
                    if not (frows['timestamp'][i] < frows['timestamp'][i + 1]):
                        print("fishy behavior at index %d" % i)
                        
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
            if dynamic_model_name == "mamarama, units: mm":
                
                #and not warned:
                #warned = True
                # logger.info("Warning: Implementing simple workaround for flydra's " \
                #       "units inconsistencies (multiplying xvel,yvel by 1000).")
                
                #srows['xvel'] *= 1000
                #srows['yvel'] *= 1000
                #srows['xvel'] *= 1000

                v = numpy.hypot(srows['xvel'], srows['yvel'], srows['zvel'])
                
                perc = [1, 5, 50, 95, 99]
                scores = map(lambda x:  scipy.stats.scoreatpercentile(v, x), perc)
                
                print "scores: %s" % map(lambda x: "%f " % x, scores)
                
                score95 = scipy.stats.scoreatpercentile(v, 95)
    
      
                if score95 < 100.0:
                    logger.debug(" score95 = %f, assuming m" % score95)
                else:
                    logger.debug(" score95 = %f, assuming mm" % score95)
                    
                    srows['xvel'] *= 0.001
                    srows['yvel'] *= 0.001
                    srows['xvel'] *= 0.001

                v = numpy.hypot(srows['xvel'], srows['yvel'], srows['zvel'])
                final_score95 = scipy.stats.scoreatpercentile(v, 95)
                
                logger.info('After much deliberation, 95%% score is %f.' % 
                            final_score95)
                
            yield obj_id, srows 
            
        except core_analysis.NotEnoughDataToSmoothError:
            logger.warning('not enough data to smooth obj_id %d, skipping.' % (obj_id,))
            continue 
        
    ca.close()
    

def get_good_files(where, pattern="*.kh5", fanout_template="fanout.xml",
                   verbose=False, confirm_problems=False):
    """ Looks for .kh5 files in the filesystem. 
    
        @where can be either:
        1) a filename
        2) a directory name
        3) a list with files and directory names
    
        Returns an array of tuples   (filename, obj_ids, stimulus)  for the valid files
    """
    
    all_files = locate_roots(pattern, where)
    
    logger.info("Found %d files with pattern %r in locations %r." % 
                (len(all_files), pattern, str(where)))
    
    good_files = []

    for filename in all_files:
        well_formed, use_obj_ids, stim_xml = \
            consider_stimulus(filename, fanout_name=fanout_template)

        if not(well_formed):
            if confirm_problems:
                logger.error("File %r not well described; skipping" % filename)
                raw_input("Are you aware of this?")
        else:
            good_files.append((filename, use_obj_ids, stim_xml))


    logger.info("Of these, %d have entries in fanout.xml" % (len(good_files),))
    
    return good_files



def  consider_stimulus(h5file, verbose_problems=False, fanout_name="fanout.xml"):
    """ Parses the corresponding fanout XML and finds IDs to use as well as the stimulus.
        Returns 3 values: valid, use_objs_ids, stimulus.  
        valid is false if something was wrong"""
   
    try:
        dir = os.path.dirname(h5file)
        fanout_xml = os.path.join(dir, fanout_name)
        if not(os.path.exists(fanout_xml)):
            if verbose_problems:
                logger.error("Stim_xml path %r not found for file %r." % 
                             (h5file, fanout_xml))
            return False, None, None

        ca = core_analysis.get_global_CachingAnalyzer()
        (obj_ids, use_obj_ids, is_mat_file, #@UnusedVariable
         data_file, extra) = ca.initial_file_load(h5file) #@UnusedVariable

        file_timestamp = timestamp_string_from_filename(h5file)

        fanout = xml_stimulus.xml_fanout_from_filename(fanout_xml)
        include_obj_ids, exclude_obj_ids = \
            fanout.get_obj_ids_for_timestamp(timestamp_string=file_timestamp)
        if include_obj_ids is not None:
            use_obj_ids = include_obj_ids
        if exclude_obj_ids is not None:
            use_obj_ids = list(set(use_obj_ids).difference(exclude_obj_ids))

        #   stim_xml = fanout.get_stimulus_for_timestamp(timestamp_string=file_timestamp)

        res = fanout._get_episode_for_timestamp(timestamp_string=file_timestamp)
        stim_fname = res[2]
        
        return True, use_obj_ids, stim_fname

    except xml_stimulus.WrongXMLTypeError:
        if verbose_problems:
            logger.error("Caught WrongXMLTypeError for %r." % file_timestamp)
        return False, None, None
    except ValueError, ex:
        if verbose_problems:
            logger.error("Caught ValueError for %r: %s" % (file_timestamp, ex))
        return False, None, None 
    except Exception, ex:
        logger.error('Not predicted exception while reading %r: %s' % (h5file, ex))
        return False, None, None
    

def timestamp_string_from_filename(filename):
    """Extracts timestamp string from filename"""
    ### TODO: check validity
    data_file_path, data_file_base = os.path.split(filename) #@UnusedVariable
    return data_file_base[4:19]

