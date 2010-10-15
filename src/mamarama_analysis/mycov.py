import numpy
import time

            

def slowcov(X, debug_period=None):
    mean = X.mean(axis=0)
    X = X - mean
    
    N = X.shape[0]
    m = X.shape[1]
    
    res = numpy.zeros((m, m), dtype=X.dtype)
    
    step = 500
    
    for i in range(int(numpy.ceil(N * 1.0 / step))):
        start = i * step
        stop = min(start + step, N)
        err = X[start:stop, :] 
        res += numpy.dot(err.T, err)
         
        if debug_period > 0:
            if not (i % debug_period):
                print "%s / %s" % (i, N)
    
    
    comp = numpy.multiply.outer(mean, mean)
    assert comp.shape == (m, m)
    
    return res / (N - 1)



def test(values):
    #print "computing covariance (shape=%s, dtype=%s)" % (str(values.shape), values.dtype)
    start = time.time()
    cov_sample1 = numpy.cov(values, rowvar=0)
    t1 = time.time() - start

    start = time.time()
    cov_sample2 = slowcov(values)
    t2 = time.time() - start
    error = numpy.max(numpy.abs(cov_sample1 - cov_sample2))
    
    speedup = t1 / t2
    
    print "shape %15s numpy.cov  %3.3f    mycov  %3.3f  error %1.4f  speedup  %.2f" % \
        (values.shape, t1, t2, error, speedup)
         

if __name__ == '__main__':
    #M = numpy.array([[1, 0], [2, 3]])
    #test(M)
    #test(numpy.ones((4, 2)))
    for rows in [10, 100, 1000, 10000, 20000]:
        test(numpy.random.rand(rows, 1398))
    
    
    
