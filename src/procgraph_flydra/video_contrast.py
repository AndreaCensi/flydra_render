import sys
from flydra_render.db import FlydraDB
from compmake import comp, batch_command, compmake_console, set_namespace
from procgraph.scripts.pg import pg
from optparse import OptionParser

description = """
This script runs the flydra_display_contrast procgraph model 
for all samples.

"""

def main():
    
    parser = OptionParser(usage=description)
    
    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")
    
    (options, args) = parser.parse_args()
     
        
    db = FlydraDB(options.db, False)
        
    directory = sys.argv[1]
    
    db = FlydraDB(directory)
    
    set_namespace('video_contrast')
    
    samples = db.list_samples()
    if not samples:
        print 'No samples found'
    
    for id in samples:
        if db.has_rows(id) and db.has_table(id, 'contrast') and \
            db.has_table(id, 'luminance'):
            config = {'sample': id, 'db': directory}
            comp(pg, 'flydra_display_contrast', config,
                 job_id="flydra_display_contrast:%s" % id)

    batch_command('make all')
    compmake_console()
    
if __name__ == '__main__':
    main()

