 
from geometric_saccade_detector.filesystem_utils import locate_roots
import tables
import os
import tempfile

from flydra_render.tables_cache import tc_open_for_reading, \
    tc_open_for_writing, tc_close

FLYDRA_ROOT = 'flydra'

class FlydraDB:
    
    def __init__(self, directory, create=True):
        
        if create:
            if not os.path.exists(directory):
                os.makedirs(directory)
        else:
            if not os.path.exists(directory):
                raise ValueError('Directory %s does not exist.' % directory)
        if not os.path.isdir(directory):
            raise ValueError('Given argument "%s" is not a directory' % directory)
    
        
        self.directory = directory
        self.index = db_summary(directory)
        # make sure we have the skeleton
        if not 'flydra' in self.index.root:
            self.index.createGroup('/', 'flydra')
        if not 'samples' in self.index.root.flydra:
            self.index.createGroup('/flydra', 'samples')
            
        self.samples = self.index.root.flydra.samples
    
    def list_samples(self):
        ''' Returns an array of samples IDs. 
            For a sample to be in here, it must at least have rows in the file.
        '''
        return list(self.samples._v_children)
    
    def has_sample(self, id):
        return id in self.samples
     
    def add_sample(self, id):
        assert not self.has_sample(id)
        sample_group = self.index.createGroup(self.samples, id)
        self.index.createGroup(sample_group, 'images')
        
    def get_sample_group(self, id):
        ''' Returns the pytables group used for this sample.
            Useful to set and retrieve attributes. '''
        assert self.has_sample(id)
        return self.samples._f_getChild(id) 
        
    def close(self):
        tc_close(self.index)

    def set_table(self, id, attname, data):
        sample_group = self.get_sample_group(id)
        filename = os.path.join(self.directory, "%s-%s.h5" % (id, attname)) 
        if os.path.exists(filename):
            #print "Removing file '%s'." % filename		
            os.unlink(filename)
        
        print "Writing on file '%s'." % filename
        f = tc_open_for_writing(filename)
        filters = tables.Filters(complevel=1, complib='zlib',
                                 fletcher32=True)
        
        rows_table = f.createTable(sample_group._v_pathname, attname,
                                   data, createparents=True,
                                   filters=filters)
                                   
        if attname in sample_group:
            # print "Removing previous link"
            sample_group._f_getChild(attname)._f_remove()
            
        self.index.createExternalLink(sample_group, attname,
                                      rows_table, warn16incompat=False)
        tc_close(f)
        
    def has_table(self, id, attname):
        assert self.has_sample(id)
        group = self.get_sample_group(id)
        return attname in group
    
    def list_tables(self, id):
        sample_group = self.get_sample_group(id)
        return list(sample_group._v_children)
        
    def get_table(self, id, attname):
        ''' Gets the table for reading. '''
        assert self.has_table(id, attname)    
        ref = self.get_sample_group(id)._f_getChild(attname)
        # dereference locally, so we keep a reference count
        filename, target = ref._get_filename_node()
        external = tc_open_for_reading(filename)
        return external.getNode(target)
        # return ref(mode='a') # dereference

    def release_table(self, table):
        ''' Releases the table (if nobody else is reading it, it
        will be closed.) '''
        tc_close(table._v_file)

    def has_attr(self, id, key):
        if not self.has_rows(id):
            return False
        rows = self.get_rows(id)
        attrs = rows._v_attrs
        have = key in attrs
        self.release_table(rows)
        return have
     
    def set_attr(self, id, key, value):
        rows = self.get_rows(id)
        attrs = rows._v_attrs
        attrs.__setattr__(key, value)
        self.release_table(rows)
 
    not_specified = 'not-specified'
    def get_attr(self, id, key, default=not_specified):
        if not self.has_attr(id, key) and \
            default != FlydraDB.not_specified:
            return default
        rows = self.get_rows(id)
        attrs = rows._v_attrs
        value = attrs.__getattr__(key)
        self.release_table(rows)
        return value
    
    def list_attr(self, id):
        if not self.has_rows(id):
            return []
        rows = self.get_rows(id)
        attrs = rows._v_attrs
        names = list(attrs._v_attrnamesuser)
        self.release_table(rows)
        return names
 
    # shortcuts for saccades and rows tables
 
    def has_saccades(self, id):
        return self.has_table(id, 'saccades')
    
    def get_saccades(self, id):
        return self.get_table(id, 'saccades')
    
    def set_saccades(self, id, table):
        return self.set_table(id, 'saccades', table)
    
    def has_rows(self, id):
        return self.has_table(id, 'rows')
    
    def get_rows(self, id):
        return self.get_table(id, 'rows')
    
    def set_rows(self, id, table):
        return self.set_table(id, 'rows', table)


def db_summary(directory):
    files = locate_roots('*.h5', directory)
    
    fid, summary_file = tempfile.mkstemp(suffix='.h5',
                                         prefix='index', dir=directory)
    
    #summary_file = os.path.join(directory, 'index.h5')
    summary = tc_open_for_writing(summary_file)
    for file in files:
        # do not consider the index itself
        if os.path.basename(file).startswith('index'):
            continue
        
        # print "Trying to open %s" % file
        f = tc_open_for_reading(file)

        if not FLYDRA_ROOT in f.root:
            print 'Ignoring file %s: no data belonging to Flydra DB' % \
                os.path.basename(file)
            continue
        
        link_everything(src=f, dst=summary,
                        src_filename=os.path.basename(file))
     
        tc_close(f)
    
    return summary
        
def link_everything(src, dst, src_filename):
    ''' Makes a link to every field '''
    for group in src.walkGroups("/"): 
        if not group._v_pathname in dst:
            parent = group._v_parent._v_pathname
            child = group._v_name
            dst.createGroup(parent, child)
            
        for table in src.listNodes(group, classname='Table'):
            parent = table._v_parent._v_pathname
            child = table._v_name

            if not table._v_pathname in dst:
                dst.createExternalLink(parent, child,
                                       table, warn16incompat=False)


    
    
    
    
