from flydra_render.db import FlydraDB
from compmake import progress
from mamarama_analysis.covariance import Expectation
import numpy

def compute_presaccade_action(db, samples, image, use_sign):
    ''' 
    db: FlydraDB directory
    samples: list of IDs
    '''
    db = FlydraDB(db)
    
    ex = Expectation()
    
    for i, id in enumerate(samples):
        progress('Computing interaction of %s' % image,
                 (i, len(samples)), "Sample %s" % id)
    
        if not (db.has_sample(id) and db.has_image(id, image) 
                and db.has_saccades(id)):
            raise ValueError('Not enough data for id %s' % id)
        
        data = db.get_image(id, image)
        values = data[:]['value']
        
        frame = data[:]['frame']
        
        saccades = db.get_saccades(id)
        
        actions = numpy.zeros(shape=(len(data),), dtype='float32')
        
        for saccade in saccades:
            final_frame = saccade['frame']
            time_passed = saccade['time_passed']
            smooth_displacement = saccade['smooth_displacement']
            
            dt = 1.0 / 60
            initial_frame = final_frame - numpy.ceil(time_passed / dt) 
            margin = 2
            final_frame -= margin
            initial_frame += margin
            
            action = smooth_displacement / time_passed
            
            if use_sign:
                action = numpy.sign(action)
                
            region = numpy.logical_and(frame >= initial_frame,
                                        frame <= final_frame)
            
            actions[region] = action 
            
        values_times_actions = numpy.zeros(shape=values.shape, dtype='float32')
        
        for i in range(len(data)):
            values_times_actions[i, :] = values[i, :] * actions[i]
            
        ex.update(values_times_actions.mean(axis=0), len(data))

    return ex.get_value()
