import numpy, time

def corr_numpy(x):
    C = numpy.dot(x.T, x)

    return C

def main():
    
    N = 10000
    
    x = numpy.random.rand(N, 1398)
    
    
    functions = [('numpy', corr_numpy)]
    
    
    for id, f in functions:
        
        start = time.clock()
        
        C = f(x)
        
        print C.shape
        T = time.clock() - start
        
        print 'method: %15s  T: %s' % (id, T)



if __name__ == '__main__':
    main()
