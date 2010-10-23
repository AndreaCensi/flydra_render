import numpy
from flydra_render.receptor_directions_buchner71 import directions
#
#def intrinsic_contrast(luminance, kernel):
#    n = len(luminance)
#    assert luminance.shape == (n,)
#    assert kernel.shape == (n, n)
#     
#    contrast = numpy.zeros(shape=(n,))
#    
#    for i in range(n):
#        # compute error
#        diff = luminance - luminance[i]
#        error = numpy.square(diff)
#        similarity = kernel[i, :]
#        weights = similarity / similarity.sum()
#        contrast[i] = (error * weights).sum()
#        
#    assert numpy.all(numpy.isfinite(contrast))
#    return contrast


def get_contrast_kernel(sigma_deg=6, eyes_interact = False):
    distance_matrix = create_distance_matrix(directions)
    sigma=numpy.radians(sigma_deg)
    kernel = numpy.exp(-(distance_matrix / sigma) )

    # do not let the two eyes interact
    if not eyes_interact:
        n = 1398/2
        kernel[0:n,n:] = 0
        kernel[n:,0:n] = 0
    
    return kernel


def intrinsic_contrast(luminance, kernel):
    n = len(luminance)
    assert luminance.shape == (n,)
    assert kernel.shape == (n, n)
     
    contrast = numpy.zeros(shape=(n,))
    
    for i in range(n):
        # compute error
        diff = luminance - luminance[i]
        error = numpy.abs(diff)
        similarity = kernel[i, :]
        weights = similarity / similarity.sum()
        contrast[i] = (error * weights).sum()
        
    assert numpy.all(numpy.isfinite(contrast))
    return contrast

#
#def get_contrast_kernel(sigma_deg, eyes_interact = False):
#    distance_matrix = create_distance_matrix(directions)
#    sigma=numpy.radians(sigma_deg)
#    kernel = numpy.exp(-numpy.square(distance_matrix / sigma) )
#
#    # do not let the two eyes interact
#    if not eyes_interact:
#        n = 1398/2
#        kernel[0:n,n:] = 0
#        kernel[n:,0:n] = 0
#    
#    return kernel


def create_distance_matrix(directions):
    n = len(directions)
    
    s = numpy.array(directions)
    
    assert s.shape == (n, 3)
    
    D = numpy.zeros(shape=(n, n))
    for i in range(n):
        
        dot_product = numpy.dot(s, s[i, :])
        
        # compensate numerical errors
        dot_product = numpy.maximum(-1, dot_product)
        dot_product = numpy.minimum(+1, dot_product)
    
        D[i, :] = numpy.arccos(dot_product)
         
    return D 