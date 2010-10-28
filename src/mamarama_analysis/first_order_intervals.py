import numpy
import scipy
import scipy.stats

# interval_function gets as arguments (FlydraDB, sample_id, rows)
# and should return a boolean array, the length of the "rows" table,
# indicating which time instant should be included in the computation.

def interval_all(flydra_db, sample_id, rows):
    N = len(rows)
    interval = numpy.ndarray(shape=(N,), dtype='bool')
    interval[:] = True
    return interval
 

def interval_fast(flydra_db, sample_id, rows):
    linear_velocity_modulus = rows[:]['linear_velocity_modulus']
    
    score95 = scipy.stats.scoreatpercentile(linear_velocity_modulus, 95)
    
    threshold = 0.1 # m/s
    
      
    if score95 < 100.0:
    #    print " score95 = %f, assuming m" % score95
        pass
    else:
    #    print " score95 = %f, assuming mm" % score95
        threshold *= 1000
    
    # interval = linear_velocity_modulus > 0.05
    interval = linear_velocity_modulus > threshold
    
    return interval


def interval_saccades(flydra_db, sample_id, rows):
    between =  interval_between_saccades(flydra_db, sample_id, rows)
    fast = interval_fast(flydra_db, sample_id, rows)
    
    return numpy.logical_and(numpy.logical_not(between), fast)


def interval_between_saccades(flydra_db, sample_id, rows):
    N = len(rows)
    interval = numpy.ndarray(shape=(N,), dtype='bool')
    interval[:] = False
    frame = rows[:]['frame']

    if not flydra_db.has_saccades(sample_id):
        raise ValueError('Saccades not present for id %s' % sample_id)

    saccades = flydra_db.get_saccades(sample_id)
        
    for saccade in saccades:
        final_frame = saccade['frame']
        time_passed = saccade['time_passed']
#            smooth_displacement = saccade['smooth_displacement']
            
        dt = 1.0 / 60
        initial_frame = final_frame - numpy.ceil(time_passed / dt) 
        margin = 2
        final_frame -= margin
        initial_frame += margin
            
        region = numpy.logical_and(frame >= initial_frame,
                                   frame <= final_frame)
            
        interval[region] = True 
            
    flydra_db.release_table(saccades)
    
    fast = interval_fast(flydra_db, sample_id, rows)
    return numpy.logical_and(interval, fast)



