import sys
from optparse import OptionParser
from compmake import comp, batch_command, compmake_console, set_namespace, \
                     parse_job_list

from flydra_db import FlydraDB
from procgraph import pg

from flydra_render import logger # XXX:

description = """

This script runs a generic ProcGraph model against
all samples in the Flydra DB.

The model should accept "db" and "sample" as parameters.

Example invocation:

    $ flydra_run_pg_model  
        --db flydra_db 
        --model flydra_display_luminance 
        --needs rows,luminance 
        --interactive [IDs]

"""

def main():
    
    parser = OptionParser(usage=description)
    
    parser.add_option("--db", default='flydra_db_directory', help="FlydraDB directory")
    parser.add_option("--model", help="ProcGraph model name.")
    parser.add_option("--needs", help="Comma-separated list of tables required",
                      default="rows,luminance")
    
    parser.add_option("--interactive",
                      help="Start compmake interactive session."
                      " Otherwise run in batch mode",
                      default=False, action="store_true")

    (options, args) = parser.parse_args()
     
        
    if options.model is None:
        print "Please specify the model."
        sys.exit(-3)
        
    print("Using FlydraDB directory %r." % options.db)
    db = FlydraDB(options.db, False)
    
    # TODO: make the storage inside options.db?
    set_namespace('run_pg_model_%s' % options.model)
    tables = options.needs.split(',')
    
    if args:
        samples = args
        for sample in samples:
            if not db.has_sample(sample):
                raise Exception('Unknown sample %r' % sample)
    else:
        samples = db.list_samples()
        
    if not samples:
        print 'No samples found'
    
    num_ok = 0
    for id in samples:
        enough = all(map(lambda t: db.has_table(id, t), tables))
        
        if not enough:
            continue 
        
        num_ok += 1  
        config = {'sample': id, 'db': options.db}
        comp(pg, options.model, config, job_id=id)

    logger.info("Found %d/%d samples with tables %s." % (num_ok, len(samples), tables))

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
            logger.info('Still %d jobs to do.' % len(todo))
            sys.exit(-2)
    
if __name__ == '__main__':
    main()
    
