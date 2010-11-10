import sys
from flydra_render.db import FlydraDB
from compmake import comp, batch_command, compmake_console, set_namespace
from procgraph.scripts.pg import pg
from optparse import OptionParser
from compmake.jobs.syntax.parsing import parse_job_list
from flydra_render import logger

description = """

This script runs a generic ProcGraph model against
all samples in the Flydra DB.

The model should accept "db" and "sample" as parameters.

Example invocation:

    $ flydra_run_pg_model  
        --db flydra_db 
        --model flydra_display_luminance 
        --needs rows,luminance 
        --interactive

"""

def main():
    
    parser = OptionParser(usage=description)
    
    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")
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
        
        
    db = FlydraDB(options.db, False)
    
    
    set_namespace('run_pg_model_%s' % options.model)
    tables = options.needs.split(',')
    
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
    
