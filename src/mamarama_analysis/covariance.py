import numpy

from compmake import progress 

from flydra_db import FlydraDB

def weighted_average(A, Aweight, B, Bweight=1):
    """ Computes the weighted average of two quantities A,B. """
    assert Aweight + Bweight > 0
    return (A * Aweight + B * Bweight) / (Aweight + Bweight)

class Expectation:
    ''' A class to compute the mean of a quantity over time '''
    def __init__(self):
        self.num_samples = 0.0
        self.value = None
        
    def update(self, val, weight=1):
        if True:
            assert weight > 0
            assert(numpy.isfinite(val).all())
        
        if  self.value is None:
            self.value = val
        else:
            self.value = weighted_average(self.value, self.num_samples, 
                                          val, weight) 
        self.num_samples += weight
        
    def get_value(self):
        return self.value 

def array_mean(x):
    return x.mean(axis=0)

def array_var(x):
    return x.var(axis=0)


def compute_mean_generic(db, samples, image, operator):
    ''' 
    db: FlydraDB directory
    samples: list of IDs
    '''
    db = FlydraDB(db, False)
    
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
        
        # print "id: %s   len: %d  %d" % (id, len(data), len(values))
        ex.update(this, len(data))
    
        results['samples'][id] = this
            
        db.release_table(data)

    results['all'] = ex.get_value()
        
    db.close()
    
    return results 

 
#            
#
#def slowcov2(X, debug_period=None):
#    mean = X.mean(axis=0)
#    
#    N = X.shape[0]
#    
#    m = X.shape[1]
#    
#    res = numpy.zeros((m, m))
#    
#    for i in range(N):
#        err = X[i, :] - mean
#        res += numpy.dot(err, err.T) / N
#        if debug_period is not None:
#            if not (i % debug_period):
#                print "%s / %s" % (i, N)
#    
#    return res
#    
