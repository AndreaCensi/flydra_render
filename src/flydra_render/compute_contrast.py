from optparse import OptionParser
from flydra_render import logger
import sys
from flydra_render.db import FlydraDB
from rfsee.rfsee_client import ClientTCP
import numpy
from flydra_render.progress import progress_bar
from flydra_render.receptor_directions_buchner71 import directions

def main():
    
    parser = OptionParser()

    parser.add_option("--db", default='flydra_render_output',
                      help="Data directory")

    parser.add_option("--nocache", help="Ignores already computed results.",
                      default=False, action="store_true")    
    
    (options, args) = parser.parse_args()
    

    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)
        
        
    distance_matrix = create_distance_matrix(directions)

        
    db = FlydraDB(options.db)
    
    if args:
        do_samples = args
    else:
        do_samples = db.list_samples()
    
    for i, sample_id in enumerate(do_samples):
        
        print 'Sample %s/%s: %s' % (i + 1, len(do_samples), sample_id)
        
        if not db.has_sample(sample_id):
            raise Exception('Sample %s not found in db.' % sample_id)
        
        if not db.has_image(sample_id, 'luminance'):
            print 'Sample %s does not have luminance; skipping.' % sample_id
            continue
        
        if db.has_image(sample_id, 'contrast') and not options.nocache:
            print 'Already computed contrast for %s; skipping' % sample_id
            continue


        luminance = db.get_image(sample_id, 'luminance')
        
        contrast = compute_contrast(luminance, distance_matrix, sigma=numpy.radians(5))
        
        db.add_image(sample_id, 'contrast', contrast)
        



def compute_contrast(luminance, distance_matrix, sigma):
    kernel = numpy.exp(-distance_matrix / sigma)
    
    contrast = numpy.ndarray(shape=luminance.shape, dtype=luminance.dtype)
    contrast[:]['time'] = luminance[:]['time']
    contrast[:]['frame'] = luminance[:]['frame']
    contrast[:]['obj_id'] = luminance[:]['obj_id']
    
    num = len(luminance)
    pbar = progress_bar('Computing contrast', num)
    
    for i in xrange(num):
        pbar.update(i)
        c = intrinsic_contrast(luminance[i]['value'], kernel)
        contrast[i]['value'][:] = c
        
    return contrast
    
def intrinsic_contrast(luminance, kernel):
    n = len(luminance)
    assert luminance.shape == (n,)
    assert kernel.shape == (n, n)
     
    contrast = numpy.zeros(shape=(n,))
    
    for i in range(n):
        # compute error
        diff = luminance - luminance[i]
        error = numpy.square(diff)
        similarity = kernel[i, :]
        weights = similarity / similarity.sum()
        contrast[i] = (error * weights).sum()
        
    assert numpy.all(numpy.isfinite(contrast))
    return contrast

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
    
    
    
    
    
    



if __name__ == '__main__':
    main()
