import os, numpy, tables, sys, warnings
from contextlib import contextmanager

# remove pytables' warning about strange table names
warnings.filterwarnings('ignore', category=tables.NaturalNameWarning)



from .tables_cache import tc_open_for_reading, tc_open_for_writing,  \
    tc_open_for_appending, tc_close
from .log import logger
from .db_index import db_summary
from .natsort import natsorted


class FlydraDBBase:
    
    def __init__(self, directory, create=False):
        
        if create:
            if not os.path.exists(directory):
                logger.info('FlydraDB does not exist in directory %s; creating.' % \
                            directory)
                os.makedirs(directory)
        else:
            if not os.path.exists(directory):
                raise ValueError('Directory %s does not exist.' % directory)
        if not os.path.isdir(directory):
            raise ValueError('Given argument "%s" is not a directory' % directory)
    
        
        self.directory = directory
        self.index = db_summary(directory)
            
        self.samples = self.index.root.flydra.samples
    
        # references count for tables checked out by clients
        # We keep them so we can close them in case of error.
        self.tc_references = {}
        
    def list_samples(self):
        ''' Returns an array of samples IDs. 
            For a sample to be in here, it must at least have rows in the file.
        '''
        return natsorted(self.samples._v_children)
    
    def has_sample(self, sample):
        return sample in self.samples
     
    def add_sample(self, sample):
        assert not self.has_sample(sample)
        sample_group = self.index.createGroup(self.samples, sample)
        self.index.createGroup(sample_group, 'images')
        
    def _get_sample_group(self, sample):
        ''' Returns the pytables group used for this sample.
            Useful to set and retrieve attributes. '''
        assert self.has_sample(sample)
        return self.samples._f_getChild(sample) 
        
    def close(self):
        if self.tc_references:
            sys.stderr.write('FlydraDB clients left %s references open:\n' % 
                             len(self.tc_references))
            for ref, num in self.tc_references.items():
                sys.stderr.write('- %d ref for %s\n' % (num, ref))
                for i in range(num): #@UnusedVariable
                    tc_close(ref)
            self.tc_references = {}
        tc_close(self.index)
        self.index = None

    def set_table(self, sample, table, data):

        sample_group = self._get_sample_group(sample)
        filename = os.path.join(self.directory, "%s-%s.h5" % (sample, table)) 
        if os.path.exists(filename):
            #print "Removing file '%s'." % filename		
            os.unlink(filename)
        
        # print "Writing on file '%s'." % filename
        f = tc_open_for_writing(filename)
        filters = tables.Filters(complevel=1, complib='zlib',
                                 fletcher32=True)
        
        rows_table = f.createTable(sample_group._v_pathname, table,
                                   data, createparents=True,
                                   filters=filters)
                                   
        if table in sample_group:
            # print "Removing previous link"
            sample_group._f_getChild(table)._f_remove()
        
        # TODO: make sure to use relative names
        self.index.createExternalLink(sample_group, table,
                                      rows_table, warn16incompat=False)
        tc_close(f)
        
    def has_table(self, sample, table):
        assert self.has_sample(sample)
        group = self._get_sample_group(sample)
        return table in group
    
    def list_tables(self, sample):
        sample_group = self._get_sample_group(sample)
        return list(sample_group._v_children)
        
    def get_table(self, sample, table, mode='r'):
        ''' Gets the table for reading or writing. 
            If you open for writing and somebody is reading it,
            an error will be thrown. '''
        assert mode in FlydraDBBase.valid_modes
    
        if not FlydraDBBase.has_table(self, sample, table):
            msg = '%r does not have table %r.' % (sample,table)
            msg += ' Available: %r' %  FlydraDBBase.list_tables(self, sample)
            raise ValueError(msg)   
        ref = self._get_sample_group(sample)._f_getChild(table)
        # dereference locally, so we keep a reference count
        filename, target = ref._get_filename_node()
        
        # resolve filename using relative names
        base = self.directory
        # not valid if we put the temp file somewhere else
        # base = os.path.dirname(self.index.filename)
        filename = os.path.join(base, filename)
        
        if mode == 'r':
            external = tc_open_for_reading(filename)
        elif mode == 'r+':
            external = tc_open_for_appending(filename)
        else:
            raise ValueError('Invalid mode "%s".' % mode)
        
        table =  external.getNode(target)
    
        ref = table._v_file
        if not ref in self.tc_references:
            self.tc_references[ref] = 0
        self.tc_references[ref] += 1
        
        return table
        # return ref(mode='a') # dereference

    def release_table(self, table):
        ''' Releases the table (if nobody else is reading it, it
        will be closed.) '''
        ref = table._v_file
        assert ref in self.tc_references
        self.tc_references[ref] -= 1
        if self.tc_references[ref] == 0:
            del self.tc_references[ref]
        tc_close(table._v_file)

    valid_modes = ['r', 'r+']
    
    @contextmanager
    def _get_attrs(self, sample, mode='r'):
        ''' Gets the node holding the attributes, and releases it afterward. '''
        assert mode in FlydraDBBase.valid_modes
        if not self.has_table(sample, 'attrs'):
            data = numpy.zeros(shape=(1,),dtype=[('dummy', 'uint8')])
            self.set_table(sample, 'attrs', data)
            
        attr_table = self.get_table(sample, 'attrs', mode=mode)
        
        yield attr_table._v_attrs
        
        self.release_table(attr_table)
        
        
    def has_attr(self, sample, key):
        with self._get_attrs(sample) as attrs:
            have = key in attrs
        return have
     
    def set_attr(self, sample, key, value):
        with self._get_attrs(sample, 'r+') as attrs:
            attrs.__setattr__(key, value)
 
    not_specified = 'not-specified'
    def get_attr(self, sample, key, default=not_specified):
        if not self.has_attr(sample, key) and \
            default != FlydraDBBase.not_specified:
            return default
        
        with self._get_attrs(sample, 'r') as attrs:
            value = attrs.__getattr__(key)
        
        return value
    
    def list_attr(self, sample):
        with self._get_attrs(sample, 'r') as attrs:
            names = list(attrs._v_attrnamesuser)
        
        return names
 
    
class FlydraDBExtra(FlydraDBBase):
    ''' This class builds on the facilities provided by FlydraDBBase 
        and implements things such as:
            - aliases 
            - sample groups and 
            - configurations. '''
            
    # shortcuts for saccades and rows tables
    def has_saccades(self, sample):
        return self.has_table(sample, 'saccades')
    
    def get_saccades(self, sample):
        return self.get_table(sample, 'saccades')
    
    def set_saccades(self, sample, table):
        return self.set_table(sample, 'saccades', table)
    
    def has_rows(self, sample):
        return self.has_table(sample, 'rows')
    
    def get_rows(self, sample):
        return self.get_table(sample, 'rows')
    
    def set_rows(self, sample, table):
        return self.set_table(sample, 'rows', table)

    
    def list_all_versions_for_table(self, table):
        """ Lists all the configurations present in the data
            for a given table. """
        versions = set()
        for sample in self.list_samples():
            if self.has_table(sample, table):
                his = self.list_versions_for_table(sample, table)
                versions.update(his)
                
        return natsorted(versions)
    
    separator = ','
    default_version_name = 'default'
    
    @staticmethod
    def name2components(s):
        """ Return name, version """
        tokens = filter(lambda x: x, s.split(','))
        assert 0 < len(tokens) <= 2
        if len(tokens)==1:
            return tokens[0], FlydraDBExtra.default_version_name
        else:
            return tokens[0], tokens[1]
                
    @staticmethod
    def components2name(table, version=None):
        if version is None:
            version = FlydraDBExtra.default_version_name
        assert not FlydraDBExtra.separator in table, \
               'Invalid raw table name %r.' % table
        assert not FlydraDBExtra.separator in version, \
               'Invalid table version %r.' % version
        
        if version == FlydraDBExtra.default_version_name:
            return table
        else:
            return '%s%s%s' % (table,  FlydraDBExtra.separator, version)
    
    def list_versions_for_table(self, sample, table):
        ''' List all the version of table possessed by a specific sample. '''
        versions = set()
        for rtable in FlydraDBBase.list_tables(self, sample):
            name, version = FlydraDBExtra.name2components(rtable)
            if name == table:
                versions.add(version)
        return natsorted(versions)
    
    
    # and now we have to reimplement table access with a version parameter
    def set_table(self, sample, table, data, version=None): 
        ''' Wraps original to add a version argument. '''
        rtable = FlydraDBExtra.components2name(table, version)
        return FlydraDBBase.set_table(self, sample=sample, table=rtable, data=data)
    
    def get_table(self, sample, table,  version=None, mode='r'):
        ''' Wraps original to add a version argument. '''
        assert mode in ['r', 'r+']
        if not self.has_table(sample, table, version):
            msg = 'Sample %r does not have version %r of table %r.' % \
                (sample, version, table)
            raise ValueError(msg)
        rtable = FlydraDBExtra.components2name(table, version)
        return FlydraDBBase.get_table(self, sample=sample, table=rtable, mode=mode)
            
    def has_table(self, sample, table, version=None):
        ''' Wraps original to add a version argument. '''
        rtable = FlydraDBExtra.components2name(table, version)
        return FlydraDBBase.has_table(self, sample=sample, table=rtable)
    
    def list_tables(self, sample):
        ''' Wraps original to hide different versions of the same tables.
            It also hides the special table 'attrs' which is used internally
            for attributes. '''
        # TODO: add possibility of specifying version?
        tables = set()
        for rtable in FlydraDBBase.list_tables(self, sample):
            name, version = FlydraDBExtra.name2components(rtable) #@UnusedVariable
            if name != 'attrs':
                tables.add(name)
        return natsorted(tables)
        
    # Group basic functions
    
    def list_groups(self):
        """ Returns a list of the groups. """
        groups = set()
        for sample in self.list_samples():
            groups.update(self.list_groups_for_sample(sample))
        return natsorted(groups)
    
    def list_groups_for_sample(self, sample, cache={}):
        """ Returns the groups to which sample belongs. """
        # FIXME: make proper memoization that can be invalidated
        if sample in cache:
            return cache[sample]
        
        # TODO: should this be a list?
        value = self.get_attr(sample, 'groups', '') 
        groups = filter(lambda x:x, value.split(','))
        result = natsorted(groups)
        cache[sample] = result
        return result
    
    def add_sample_to_group(self, sample, group):
        groups = set(self.list_groups_for_sample(sample))
        groups.add(group)
        value = ",".join(natsorted(groups))
        self.set_attr(sample, 'groups', value)
    # todo: remove
        
    def list_samples_for_group(self, group):
        """ Lists the samples in the given group. """
        samples = []
        for sample in self.list_samples():
            if group in self.list_groups_for_sample(sample):
                samples.append(sample)
        return natsorted(samples)
    
    #
    # Group utility functions
    #
    def list_tables_for_group(self, group, cache={}):
        ''' Retuns a list of all the tables owned by the samples 
            in this group. '''
        tables = set()
        for sample in self.list_samples_for_group(group):
            tables.update(self.list_tables(sample))
        
        result = natsorted(tables)
        
        return result

    def group_has_table(self, group, table, version=None):
        ''' Tests that all samples in the group have this table. '''
        samples = self.list_samples_for_group(group)
        for sample in samples:
            if not self.has_table(sample, table, version):
                return False
        else:
            return True
        
    def list_versions_for_table_in_group(self, group, table):
        ''' List all the version of table possessed by the samples
            in a specific group. Note that not necesseraly all samples
            have all versions. '''
        samples = self.list_samples_for_group(group)
        assert samples, 'Empty group %r.' % group
        versions = set()
        for sample in samples:
            versions.update(self.list_versions_for_table(sample, table))
        return natsorted(versions)

FlydraDB = FlydraDBExtra



@contextmanager
def safe_flydra_db_open(flydra_db_directory, create=False):
    ''' Context manager to remember to close the .h5 files. '''
    db = FlydraDB(flydra_db_directory, create)
    try:
        yield db
    finally:
        db.close()
        
