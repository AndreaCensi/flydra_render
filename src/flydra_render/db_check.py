import sys
from flydra_render.db import FlydraDB
import numpy

def main():
    directory = sys.argv[-1]

    db = FlydraDB(directory)  
    
    samples = db.list_samples()
    if not samples:
        print 'No samples found'
    
    for id in samples:
        print "Sample %s" % id
        
        rows = db.get_rows(id)
        
        for table in db.list_tables(id):    
            if table != 'images':
                t = db.get_table(id, table)
                print ' - %s: %d' % (table, len(t))
                
                if len(t) == len(rows):
                    # check frame is ok
                    ok = numpy.all(t[:]['frame'] == rows[:]['frame'])
                
                    if not ok:
                        print 'WARNING: table does not pass consistency check'
                db.release_table(t)
        
        db.release_table(rows)
        
        for att in db.list_attr(id):
            s = str(db.get_attr(id, att))
            if len(s) > 50:
                s = s[0:50] + ' ...'
            print ' - attribute %s = %s ' % (att, s)
        
    db.close()
    
if __name__ == '__main__':
    main()
