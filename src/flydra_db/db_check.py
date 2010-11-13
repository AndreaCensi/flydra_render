import numpy
from optparse import OptionParser

from flydra_db import FlydraDB


def main():
    parser = OptionParser()
    
    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

    parser.add_option("--extensive", help="Does an extensive consistency check",
                      default=False, action="store_true")
    
    (options, args) = parser.parse_args() #@UnusedVariable
        

    db = FlydraDB(options.db)  
    
    if args:
        samples = args
    else:
        samples = db.list_samples()
        
    if not samples:
        print 'No samples found'
    
    for id in samples:
        if not db.has_sample(id):
            raise Exception('Sample "%s" not found.' % id)
        
        print "Sample %s" % id
        
        if db.has_table(id, 'rows'):
            rows = db.get_table(id, 'rows')
        else:
            rows = None
        
        for table in db.list_tables(id):
            t = db.get_table(id, table)
            print ' - %s: %d' % (table, len(t))
            
            if options.extensive and rows and (len(t) == len(rows)):
                # check frame is ok
                ok = numpy.all(t[:]['frame'] == rows[:]['frame'])
            
                if not ok:
                    print 'WARNING: table does not pass consistency check'
            db.release_table(t)
        
        if rows:
            db.release_table(rows)
        
        for att in db.list_attr(id):
            s = (db.get_attr(id, att)).__repr__()
            if len(s) > 50:
                s = s[0:50] + ' ...'
            print ' - attribute %s = %s ' % (att, s)
        
    db.close()
    
if __name__ == '__main__':
    main()