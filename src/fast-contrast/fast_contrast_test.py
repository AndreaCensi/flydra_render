from fast_contrast import intrinsic_contrast as ic_fast

from flydra_render.contrast import get_contrast_kernel
from flydra_render.contrast import intrinsic_contrast as ic_slow
import numpy
import time

kernel = get_contrast_kernel(sigma_deg=6, eyes_interact=False)
kernel = kernel.astype('float32')


y = numpy.random.rand(1398).astype('float32')

c1 = ic_fast(y, kernel)
c2 = ic_slow(y, kernel)

print "Error: %.5f" % numpy.linalg.norm(c1 - c2, ord=numpy.inf)


print "Trying fast:" 

N = 100
t0 = time.clock()

for i in range(N):
    c1 = ic_fast(y, kernel)
    
t1 = time.clock() - t0

print "Fast: %.2f seconds (%.1f ops/second)" % (t1, N / t1)

t0 = time.clock()
for i in range(N):
    c2 = ic_slow(y, kernel)
 
t2 = time.clock() - t0

print "Slow: %.2f seconds  (%.1f ops/second)" % (t2, N / t2)


print "Speedup=  %.1fx" % (t2 / t1)
