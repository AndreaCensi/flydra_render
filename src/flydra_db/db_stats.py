from optparse import OptionParser

from flydra_db import FlydraDB


def main():
    parser = OptionParser()
    
    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")
    parser.add_option("--check_versions",
                      help="Checks that all samples in a group have the same"
                         " versions of a table",
                      default=False, action="store_true")

    (options, args) = parser.parse_args() #@UnusedVariable
        

    db = FlydraDB(options.db)  
    
    groups = db.list_groups()
    
    for group in groups:
        samples = db.list_samples_for_group(group)
        
        print("- group %r: %d samples" % (group, len(samples)))
    
        tables = db.list_tables_for_group(group)
        for table in tables:
            versions = db.list_versions_for_table_in_group(group, table)
            print('  - table %r: %d versions' % (table, len(versions)))
            if options.check_versions:
                for version in versions:
                    if not db.group_has_table(group, table, version):
                        print(' (!) version %r not shared by all' % version)

    db.close()
    
if __name__ == '__main__':
    main()
