import sys
from flydra_render.db import FlydraDB

def main():
    directory = sys.argv[-1]

    db = FlydraDB(directory)
    
    samples = db.list_samples()
    if not samples:
        print 'No samples found'
    
    for sample in samples:
        rows = db.get_rows(sample)
        print "Sample %s: %d rows" % (sample, len(rows))
        images = db.list_images(sample)
        if not images:
            print ' (no images found)'
        for image in images:
            im = db.get_image(sample, image)
            print " - image %s: %d rows" % (image, len(im))

    db.close()
    
if __name__ == '__main__':
    main()
