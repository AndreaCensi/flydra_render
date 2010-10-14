import sys
from flydra_render.db import FlydraDB
from compmake import comp, batch_command, compmake_console, set_namespace
from procgraph.scripts.pg import pg


def main():
    if len(sys.argv) != 2:
        print "Usage: %s <db>" % sys.argv[0]
        sys.exit(-1)
        
    directory = sys.argv[1]
    
    db = FlydraDB(directory)
    
    set_namespace('video_contrast')
    
    samples = db.list_samples()
    if not samples:
        print 'No samples found'
    
    for id in samples:
        if db.has_rows(id) and db.has_image(id, 'contrast') and \
            db.has_image(id, 'luminance'):
            config = {'sample': id, 'db': directory}
            comp(pg, 'flydra_display_contrast', config,
                 job_id="flydra_display_contrast:%s" % id)

    batch_command('make all')
    compmake_console()
    
if __name__ == '__main__':
    main()
