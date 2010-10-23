import sys, numpy
from optparse import OptionParser

from flydra_render import logger
from flydra_render.db import FlydraDB
from flydra_render.progress import progress_bar
from flydra_render.receptor_directions_buchner71 import directions
from flydra_render.contrast import get_contrast_kernel, intrinsic_contrast

def main():
    
    parser = OptionParser()

    parser.add_option("--db", default='flydra_render_output',
                      help="Data directory")

    parser.add_option("--nocache", help="Ignores already computed results.",
                      default=False, action="store_true")    
    
    parser.add_option("--sigma", help="Kernel spread (degrees)",
                      type="float", default=3)
   
    parser.add_option("--source", default='luminance', help="Source table")
    parser.add_option("--target", default='contrast', help="Destination table")

    
    (options, args) = parser.parse_args()
    

    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)

    
    kernel = get_contrast_kernel(sigma_deg=options.sigma)
    
    db = FlydraDB(options.db)
    
    if args:
        do_samples = args
    else:
        do_samples = db.list_samples()
        do_samples = filter(lambda x: db.has_table(x, options.source),
                            do_samples)
        
    if not do_samples:
        raise Exception('No samples with table "%s" found. ' % options.source)
    
    for i, sample_id in enumerate(do_samples):
        
        logger.info( 'Sample %s/%s: %s' % (i + 1, len(do_samples), sample_id))
        
        if not db.has_sample(sample_id):
            raise Exception('Sample %s not found in db.' % sample_id)
        
        if not db.has_table(sample_id, options.source):
            raise Exception('Sample %s does not have table %s; skipping.' \
                            % (sample_id, options.source))
        
        if db.has_table(sample_id, options.target) and not options.nocache:
            logger.info('Already computed "%s" for %s; skipping' % \
                (options.target, sample_id))
            continue


        luminance = db.get_table(sample_id, options.source)
        
    
        contrast = compute_contrast(luminance, kernel)
        
        db.set_table(sample_id, options.target, contrast)
        
        db.release_table(luminance)
        

def compute_contrast(luminance, kernel):
    
    
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

    


if __name__ == '__main__':
    main()
