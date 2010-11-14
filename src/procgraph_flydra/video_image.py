import sys
from optparse import OptionParser

from flydra_db import FlydraDB

from compmake import comp, set_namespace, compmake_console, batch_command
from compmake.jobs.syntax.parsing import parse_job_list

from procgraph.scripts.pg import pg

def main():
    
    parser = OptionParser()

    parser.add_option("--db", default='flydra_db', help="Data directory")

    parser.add_option("--image", help="Which image to plot.")
    
    parser.add_option("--filter", help="Which procgraph filter to use to plot.",
                      default="flydra_simple_video_filter")
  
    parser.add_option("--interactive",
                      help="Start compmake interactive session."
                      " Otherwise run in batch mode",
                      default=False, action="store_true")

  
    (options, args) = parser.parse_args()
    
    if options.image is None:
        print "Usage: %s [--db DB] --image <image> [ids]" % sys.argv[0]
        sys.exit(-1)
            
    db = FlydraDB(options.db)
    
    set_namespace('video_image_%s' % options.image)
    
    if args:
        samples = args
    else:
        # look for samples with the rows table
        samples = db.list_samples()
        samples = filter(lambda x: db.has_table(x, options.image), samples)
    
    if not samples:
        raise Exception('No samples found at all with available image "%s".' % \
            options.image)
    
    for id in samples:
        if  not db.has_table(id, options.image):
            raise Exception('Sample %s does not have table "%s".' % 
                            (id, options.image))
            
        config = {'sample': id,
                  'db': options.db,
                  'image': options.image,
                  'filter': options.filter}
        comp(pg, 'flydra_simple_video', config,
             job_id="%s" % id)



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
