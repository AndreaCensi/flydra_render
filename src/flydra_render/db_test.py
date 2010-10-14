import sys
from flydra_render.db import FlydraDB

def main():
    directory = sys.argv[-1]

    db = FlydraDB(directory)
    
    samples = db.list_samples()
    if not samples:
        print 'No samples found'
    
    for id in samples:
        print "Sample %s" % id
        if db.has_rows(id):
            print ' - rows: %d' % len(db.get_rows(id))
        if db.has_saccades(id):
            print ' - saccades: %d' % len(db.get_saccades(id))
        
        images = db.list_images(id)
#        if not images:
#            print '   (no images found)'
        for image in images:
            im = db.get_image(id, image)
            print " - image %s: %d rows" % (image, len(im))

    db.close()
    
if __name__ == '__main__':
    main()
