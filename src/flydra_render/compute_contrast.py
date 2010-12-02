import numpy
from optparse import OptionParser

from flydra_db import FlydraDB
from flydra_db.progress import progress_bar

from . import logger
from .contrast import get_contrast_kernel

try:
    from fast_contrast import intrinsic_contrast #@UnresolvedImport @UnusedImport
except:
    logger.error('I cannot load the "fast_contrast" extension. '
                 'I will fall back on the python implementation (20x slower).')
    from  .contrast  import intrinsic_contrast  #@UnusedImport @Reimport


def main():
    
    parser = OptionParser()

    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

    parser.add_option("--nocache", help="Ignores already computed results.",
                      default=False, action="store_true")    
    
    parser.add_option("--sigma", help="Kernel spread (degrees)",
                      type="float", default=6)
   
    parser.add_option("--source", default='luminance', help="Source table")
    parser.add_option("--target", default='contrast', help="Destination table")

    
    (options, args) = parser.parse_args()


    kernel = get_contrast_kernel(sigma_deg=options.sigma, eyes_interact=False)
    kernel = kernel.astype('float32').copy('C')
    
    db = FlydraDB(options.db, False)
    
    if args:
        do_samples = args
    else:
        do_samples = db.list_samples()
        do_samples = filter(lambda x: db.has_table(x, options.source),
                            do_samples)
        
        
    if not do_samples:
        raise Exception('No samples with table "%s" found. ' % options.source)
    
    for i, sample_id in enumerate(do_samples):
        
        logger.info('Sample %s/%s: %s' % (i + 1, len(do_samples), sample_id))
        
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
    
        contrast = compute_contrast_for_table(luminance, kernel)
        
        db.set_table(sample_id, options.target, contrast)
        
        db.release_table(luminance)
    db.close()

def compute_contrast_for_table(luminance, kernel): 
    contrast = numpy.ndarray(shape=luminance.shape, dtype=luminance.dtype)
    contrast[:]['time'] = luminance[:]['time']
    contrast[:]['frame'] = luminance[:]['frame']
    contrast[:]['obj_id'] = luminance[:]['obj_id']
    
    num = len(luminance)
    pbar = progress_bar('Computing contrast', num)
    
    for i in xrange(num):
        pbar.update(i)
        y = luminance[i]['value'].astype('float32')
        c = intrinsic_contrast(y, kernel)
        contrast[i]['value'][:] = c
        
    return contrast


if __name__ == '__main__':
    main()

