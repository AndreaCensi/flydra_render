import numpy

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
    interval = linear_velocity_modulus > 0.05
    return interval
