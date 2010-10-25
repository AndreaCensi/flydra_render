from optparse import OptionParser
import sys
from flydra_render.db import FlydraDB
from flydra_render import logger
import scipy
import scipy.stats


description = """ This script checks that some statistics
 make sense. """

def main():
    
    
    parser = OptionParser(usage=description)

    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

    (options, args) = parser.parse_args() #@UnusedVariable
    
    if options.db is None:
        logger.error('Please specify  a directory using --db.')
        sys.exit(-1)

    db = FlydraDB(options.db)
    
    for sample in db.list_samples():
        if not db.has_rows(sample):
            continue
        
        rows = db.get_rows(sample)
        
        v = rows[:]['linear_velocity_modulus']
        
        perc = [1,5,95,99]
        
        print "Sample %s" % sample
        
        print " linear_velocity_modulus"
        for p in perc:
            s = scipy.stats.scoreatpercentile(v,p)
            print ' - %2d%%   %.3f m/s' % (p, s)
        

        
        
        
        db.release_table(rows)



