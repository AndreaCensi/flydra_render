import sys
from flydra_render.db import FlydraDB

def main():
    directory = sys.argv[-1]

    db = FlydraDB(directory)
    db = FlydraDB(directory) 
    db = FlydraDB(directory)  
    
    samples = db.list_samples()
    if not samples:
        print 'No samples found'
    
    for id in samples:
        print "Sample %s" % id
        
        for table in db.list_tables(id):    
            if table != 'images':
                t = db.get_table(id, table)
                print ' - %s: %d' % (table, len(t))
                db.release_table(t)
        
        for att in db.list_attr(id):
            s = str(db.get_attr(id, att))
            if len(s) > 50:
                s = s[0:50] + ' ...'
            print ' - attribute %s = %s ' % (att, s)
        
    db.close()
    
if __name__ == '__main__':
    main()
