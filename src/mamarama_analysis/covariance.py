from flydra_render.db import FlydraDB
import numpy
from compmake.jobs.progress import progress
#from mamarama_analysis.mycov import slowcov


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
    
    for i, id in enumerate(samples):
        progress('Computing mean %s' % image,
                 (i, len(samples)), "Sample %s" % id)
    
        if not (db.has_sample(id) and db.has_table(id, image)):
            raise ValueError('No table "%s" for id %s' % (image, id))
        
        data = db.get_table(id, image)
        
        values = data[:]['value']
        
        ex.update(values.mean(axis=0), len(data))
        
        db.release_table(data)

    return ex.get_value()
            

def array_mean(x):
    return x.mean(axis=0)

def array_var(x):
    return x.var(axis=0)


def compute_mean_generic(db, samples, image, operator):
    ''' 
    db: FlydraDB directory
    samples: list of IDs
    '''
    db = FlydraDB(db)
    
    results = { 'samples': {} }
    
    ex = Expectation()
    
    for i, id in enumerate(samples):
        progress('Computing mean %s' % image,
                 (i, len(samples)), "Sample %s" % id)
    
        if not (db.has_sample(id) and db.has_table(id, image)):
            raise ValueError('No table "%s" for id %s' % (image, id))
        
        data = db.get_table(id, image)
        
        values = data[:]['value']
        
        this = operator(values)
        
        ex.update(this, len(data))
    
        results['samples'][id] = this
            
        db.release_table(data)

    results['all'] = ex.get_value()
        
    return results 


            

def compute_image_var(db, samples, image):
    ''' Computes the variance (not COVariance) of an image table.
    S
    db: FlydraDB directory
    samples: list of IDs
    '''
    db = FlydraDB(db)
    
    ex = Expectation()
    
    for i, id in enumerate(samples):
        progress('Computing variance of %s' % image,
                 (i, len(samples)), "Sample %s" % id)
    
        if not (db.has_sample(id) and db.has_table(id, image)):
            raise ValueError('No table "%s" for id %s' % (image, id))
        
        data = db.get_table(id, image)
        
        values = data[:]['value']
        
        ex.update(values.var(axis=0), len(data))
        
        db.release_table(data)

    return ex.get_value()
                        
            
            
def compute_image_cov(db, samples, image):
    ''' 
    db: FlydraDB directory
    samples: list of IDs
    mean: already computed mean
    '''
    db = FlydraDB(db)
    
    ex = Expectation()
    
    for i, id in enumerate(samples):
        progress('Computing covariance of %s' % image,
                 (i, len(samples)), "Sample %s" % id)
        
        if not (db.has_sample(id) and db.has_table(id, image)):
            raise ValueError('Not enough data for id %s' % id)
        
        data = db.get_table(id, image)
        
        #print "copying values (%s)" % len(data)
        #values = numpy.array().copy()
        #print "computing covariance (shape=%s, dtype=%s)" % (str(values.shape), values.dtype)
        values = data[:]['value']
        
        #cov_sample = slowcov(values)
        cov_sample = numpy.cov(values, rowvar=0) 
         
        ex.update(cov_sample, len(data))

        db.release_table(data)

    return ex.get_value()
            
    
    

            

def slowcov2(X, debug_period=None):
    mean = X.mean(axis=0)
    
    N = X.shape[0]
    
    m = X.shape[1]
    
    res = numpy.zeros((m, m))
    
    for i in range(N):
        err = X[i, :] - mean
        res += numpy.dot(err, err.T) / N
        if debug_period is not None:
            if not (i % debug_period):
                print "%s / %s" % (i, N)
    
    return res
    
