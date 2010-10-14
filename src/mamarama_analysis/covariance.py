from flydra_render.db import FlydraDB
import numpy


def weighted_average(A, Aweight, B, Bweight=1):
    """ Computes the weighted average of two quantities A,B. """
    return (A * Aweight + B * Bweight) / (Aweight + Bweight)

class Expectation:
    ''' A class to compute the mean of a quantity over time '''
    def __init__(self):
        self.num_samples = 0.0
        self.value = None
        
    def update(self, val, weight=1):
        if  self.value is None:
            self.value = val
        else:
            self.value = weighted_average(self.value, self.num_samples, val, weight) 
        self.num_samples += weight
        
    def get_value(self):
        return self.value


def compute_image_mean(db, samples, image):
    ''' 
    db: FlydraDB directory
    samples: list of IDs
    '''
    db = FlydraDB(db)
    
    ex = Expectation()
    
    for id in samples:
        if not (db.has_sample(id) and db.has_image(id, image)):
            raise ValueError('Not enough data for id %s' % id)
        
        data = db.get_image(id, image)
        
        values = data[:]['value']
        
        ex.update(values.mean(axis=0), len(data))

    return ex.get_value()
            
            
def compute_image_cov(db, samples, image):
    ''' 
    db: FlydraDB directory
    samples: list of IDs
    mean: already computed mean
    '''
    db = FlydraDB(db)
    
    ex = Expectation()
    
    for id in samples:
        if not (db.has_sample(id) and db.has_image(id, image)):
            raise ValueError('Not enough data for id %s' % id)
        
        data = db.get_image(id, image)
        
        values = data[:]['value']
         
        ex.update(numpy.cov(values, rowvar=0), len(data))

    return ex.get_value()
            
            
        
        
    
