import numpy,scipy.stats

from compmake import progress

from flydra_db import FlydraDB

from . import logger

def get_all_data_for_signal(db, samples, interval_function, 
                            signal, signal_component):
    
    db = FlydraDB(db, False)
    
    all = []
    for id in samples:
        
        if not db.has_rows(id):
            logger.warning('Could not find rows table for %s; skipping.' % 
                           (id))
            continue
        
        rows_table = db.get_rows(id)
        
        try:
            interval = interval_function(db, id, rows_table) 
        except Exception as e:
            logger.warning('Cannot compute interval for sample %s: %s '\
                           % (id, e))
            db.release_table(rows_table)
            continue
        
        rows = rows_table[interval]
        
        s = extract_signal(rows, signal, signal_component)
        
        all.append(s)
        
        db.release_table(rows_table)
    
    
    
    db.close()
    
    return numpy.concatenate(all)
        
        
def extract_signal(rows, signal, signal_component):
    actions = numpy.zeros(shape=(len(rows),), dtype='float32')
    for i in range(len(rows)):
        if signal_component is not None:
            actions[i] = rows[i][signal][signal_component]
        else:
            actions[i] = rows[i][signal]
    return actions
    
    
def enumerate_data(db, samples, interval_function, image, 
                   signal, signal_component,
                       signal_op, what='enumerate_data'):
    for k, id in enumerate(samples):
        progress(what, (k, len(samples)), "Sample %s" % id)
        
        if not db.has_rows(id):
            logger.warning('Could not find rows table for %s; skipping.' % 
                           (id))
            continue
        
        if not db.has_table(id, image):
            logger.warning('Could not find table "%s" for %s; skipping.' % 
                           (image, id))
            continue
        
        rows_table = db.get_rows(id)
        image_table = db.get_table(id, image)
        image_values = image_table[:]['value']
        
        try:
            interval = interval_function(db, id, rows_table) 
        except Exception as e:
            logger.warning('Cannot compute interval for sample %s: %s '\
                           % (id, e))
            db.release_table(rows_table)
            continue
        
        if numpy.logical_not(interval).all():
            logger.warning('Sample %s with interval function "%s" '
                           'gives empty subset; skipping. ' %  
                           (id, interval_function.__name__))
            db.release_table(rows_table)
            continue
        
        if False:
            percentage = numpy.mean(interval * 1.0) * 100
            logger.info('Sample %s: function "%s" selects %.1f%% of data.' % 
                        (id, interval_function.__name__, percentage)) 
        
        # subset everything
        image_values = image_values[interval]
        rows = rows_table[interval]
        
        # get the action vector
        actions = extract_signal(rows, signal, signal_component)
        
        # remove the tails
        actions, removed_percentage = cut_tails(actions, percent=0.3)
        
        if removed_percentage > 1:
            logger.warning('Too much tail removed (%.3f%%) for %s/%s,' % 
                           (removed_percentage, id, signal))
                    
        actions = signal_op(actions)
    
        yield id, actions, image_values

        
        db.release_table(rows_table)
        db.release_table(image_table)
        
        # use only one sample (for debugging)
        # break
        
  

def cut_tails(x, percent=0.1):
    ''' Removes the tails correspondint to the top and bottom
        percentile. 
        Returns a tuple (x', percentage_removed).
        
    '''
    lower = scipy.stats.scoreatpercentile(x, percent)
    upper = scipy.stats.scoreatpercentile(x, 100-percent)
    
    remove_upper = x > upper
    remove_lower = x < lower
    
    x[remove_upper] = upper
    x[remove_lower] = lower
    
    remove = numpy.logical_or(remove_upper, remove_lower)
    percentage_removed = (remove*1.0).mean() * 100
    
    return x, percentage_removed

