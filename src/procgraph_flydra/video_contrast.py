import sys
from optparse import OptionParser

from flydra_db import FlydraDB

from compmake import comp, batch_command, compmake_console, set_namespace, \
                     parse_job_list

from procgraph import pg

description = """
This script runs the flydra_display_contrast procgraph model 
for all samples.

"""

def main():
    
    parser = OptionParser(usage=description)
    
    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")
    
    parser.add_option("--interactive",
                      help="Start compmake interactive session."
                      " Otherwise run in batch mode",
                      default=False, action="store_true")

    (options, args) = parser.parse_args() #@UnusedVariable
     
        
    db = FlydraDB(options.db, False)
    
    set_namespace('video_contrast')
    
    samples = db.list_samples()
    if not samples:
        print 'No samples found'
    
    for id in samples:
        if db.has_rows(id) and db.has_table(id, 'contrast') and \
            db.has_table(id, 'luminance'):
            config = {'sample': id, 'db': options.db}
            comp(pg, 'flydra_display_contrast', config,
                 job_id="flydra_display_contrast:%s" % id)

    if options.interactive:
        # start interactive session
        compmake_console()
    else:
        # batch mode
        # try to do everything
        batch_command('make all')
        # start the console if we are not done
        # (that is, make all failed for some reason)
        todo = list(parse_job_list('todo')) 
        if todo:
            print('Still %d jobs to do.' % len(todo))
            sys.exit(-2)
    
if __name__ == '__main__':
    main()

