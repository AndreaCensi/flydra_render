import numpy
from compmake import progress

from flydra_render.db import FlydraDB
from mamarama_analysis.covariance import Expectation
from mamarama_analysis import logger


def compute_signal_correlation(
        db,
        samples,
        interval_function,
        image,
        signal,
        signal_component,
        signal_op
                        ):
    
    db = FlydraDB(db)

    ex = Expectation()
    
    num_samples_used = 0
    
    for i, sample_id in enumerate(samples):
        progress('Computing interaction of %s' % image,
                 (i, len(samples)), "Sample %s" % id)
        
        rows = db.get_rows(id)
        
        if not db.has_table(id, image):
            logger.warning('Could not find table "%s" for %s; skipping.' % 
                           (image, id))
        
        image_table = db.get_table(id, image)
        image_values = image_table[:]['value']
        
        try:
            interval = interval_function(db, id, rows) 
        except Exception as e:
            logger.warning('Cannot compute interval for sample %s: %s '\
                           % (sample_id, e))
            continue
        
        # subset everything
        
        image_values = image_values[interval]
        rows = rows[interval]
        
        # get the action vector
        actions = numpy.zeros(shape=(len(rows),), dtype='float32')
        for i in range(len(rows)):
            if signal_component is not None:
                actions[i] = rows[i][signal][signal_component]
            else:
                actions[i] = rows[i][signal]
        
        values_times_actions = \
            numpy.zeros(shape=image_values.shape, dtype='float32')
            
        for i in range(len(rows)):
            values_times_actions[i, :] = image_values[i, :] * actions[i]
        
        db.release_table(rows)
        db.release_table(image_table)
        
        num_samples_used += 1
        
        ex.update(values_times_actions.mean(axis=0), len(rows))

    logger.info('In total, used %d/%d samples in the group. ' % 
                (num_samples_used, len(samples)))

    return ex.get_value()


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


def compute_rawcorr(db, samples, image, signal, signal_index, use_sign):
    db = FlydraDB(db)
    
    ex = Expectation()
    
    for i, id in enumerate(samples):
        progress('Computing interaction of %s with %s (sign=%s)' % 
                 (image, signal, use_sign),
                 (i, len(samples)), "Sample %s" % id)
    
        if not (db.has_sample(id) and db.has_image(id, image) 
                and db.has_rows(id)):
            raise ValueError('Not enough data for id %s' % id)
        
        data = db.get_image(id, image)
        values = data[:]['value']
        rows = db.get_rows(id)
        
        actions = numpy.zeros(shape=(len(data),), dtype='float32')
        for i in range(len(data)):
            if signal_index is not None:
                actions[i] = rows[i][signal][signal_index]
            else:
                actions[i] = rows[i][signal]

        if use_sign:
            actions = numpy.sign(actions)
            
        values_times_actions = numpy.zeros(shape=values.shape, dtype='float32')
        for i in range(len(data)):
            values_times_actions[i, :] = values[i, :] * actions[i]
            
        ex.update(values_times_actions.mean(axis=0), len(data))

    return ex.get_value()
