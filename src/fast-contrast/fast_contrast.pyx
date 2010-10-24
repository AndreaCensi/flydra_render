cdef extern from "numpy/arrayobject.h":
    pass
import numpy as np
cimport numpy as np
import cython

cdef extern from "math.h":
    double fabs(double)


#
#
#def intrinsic_contrast(np.ndarray[np.float32_t, ndim=1] luminance,
#                       np.ndarray[np.float32_t, ndim=2] kernel):
#    cdef int n
#    n = len(luminance)
#     
#    contrast = np.zeros(shape=(n,))
#    
#    for i in range(n):
#        # compute error
#        diff = luminance - luminance[i]
#        error = np.abs(diff)
#        similarity = kernel[i, :]
#        weights = similarity / similarity.sum()
#        contrast[i] = (error * weights).sum()
#        
#    return contrast



@cython.boundscheck(False)
@cython.wraparound(False)
def intrinsic_contrast(np.ndarray[np.float32_t, ndim=1, mode="c"] luminance,
                       np.ndarray[np.float32_t, ndim=2, mode="c"] kernel):
    cdef int n
    cdef Py_ssize_t i
    cdef Py_ssize_t j
    cdef float con
    cdef float w
    cdef np.ndarray[np.float32_t, ndim = 1] contrast
    
    n = len(luminance)
     
    contrast = np.zeros(shape=(n,), dtype='float32')
    
    for i in range(n):
        # compute error
        con = 0
        w = 0
        for j in range(n):
            con += fabs(luminance[j] - luminance[i]) * kernel[i, j]
            w += kernel[i, j]
        
        #error = np.abs(diff)
        #similarity = kernel[i, :]
        #weights = similarity / similarity.sum()
        contrast[i] = con / w 
        
    return contrast







