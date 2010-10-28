 
from geometric_saccade_detector.filesystem_utils import locate_roots
import tables
import os
import tempfile

from flydra_render.tables_cache import tc_open_for_reading, \
    tc_open_for_writing,tc_open_for_appending, tc_close
import shutil
from flydra_render import logger
from flydra_render.progress import progress_bar
from contextlib import contextmanager
import numpy

FLYDRA_ROOT = 'flydra'

class FlydraDB:
    
    def __init__(self, directory, create=True):
        
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
        
        # print "Writing on file '%s'." % filename
        f = tc_open_for_writing(filename)
        filters = tables.Filters(complevel=1, complib='zlib',
                                 fletcher32=True)
        
        rows_table = f.createTable(sample_group._v_pathname, attname,
                                   data, createparents=True,
                                   filters=filters)
                                   
        if attname in sample_group:
            # print "Removing previous link"
            sample_group._f_getChild(attname)._f_remove()
        
        # TODO: make sure to use relative names
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
        
    def get_table(self, id, attname, mode='r'):
        ''' Gets the table for reading or writing. 
            If you open for writing and somebody is reading it,
            an error will be thrown. '''
        assert self.has_table(id, attname)    
        ref = self.get_sample_group(id)._f_getChild(attname)
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
            
        return external.getNode(target)
        # return ref(mode='a') # dereference

    def release_table(self, table):
        ''' Releases the table (if nobody else is reading it, it
        will be closed.) '''
        tc_close(table._v_file)

    @contextmanager
    def _get_attrs(self, id, mode='r'):
        ''' Gets the node holding the attributes, and releases it afterward. '''
        if not self.has_table(id, 'attrs'):
            data = numpy.zeros(shape=(1,),dtype=[('dummy', 'uint8')])
            self.set_table(id, 'attrs', data)
            
        attr_table = self.get_table(id, 'attrs', mode)
        
        yield attr_table._v_attrs
        
        self.release_table(attr_table)
        
        
    def has_attr(self, id, key):
        with self._get_attrs(id) as attrs:
            have = key in attrs
        return have
     
    def set_attr(self, id, key, value):
        with self._get_attrs(id, 'r+') as attrs:
            attrs.__setattr__(key, value)
 
    not_specified = 'not-specified'
    def get_attr(self, id, key, default=not_specified):
        if not self.has_attr(id, key) and \
            default != FlydraDB.not_specified:
            return default
        
        with self._get_attrs(id, 'r+') as attrs:
            value = attrs.__getattr__(key)
        
        return value
    
    def list_attr(self, id):
        with self._get_attrs(id, 'r+') as attrs:
            names = list(attrs._v_attrnamesuser)
        
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
    '''
    - If <DB>/index.h5 is already and it is updated (more recent than directory),
      make a copy of it in <DB>/indices/    
    
    '''
    
    summary_file = os.path.join(directory, 'index.h5')

    # directory for private indices    
    temp_dir = os.path.join(directory, 'indices')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    # This will be our private index    
    my_summary = tempfile.NamedTemporaryFile(suffix='.h5_priv', prefix='.index', dir=temp_dir)
     # , dir=temp_dir)
    my_summary_file = my_summary.name

    #   fid, my_summary_file = tempfile.mkstemp(suffix='.h5_priv',
    #                      prefix='index', dir=temp_dir)

    # logger.info('Temporary file: %s' % my_summary_file)

    # if it does not exist or it is updated, recreate it 
    if not os.path.exists(summary_file) or \
        os.path.getmtime(directory) > os.path.getmtime(summary_file):
    
        logger.info('Summary file %s out of date or not existing; recreating.'%\
                    summary_file)    
        
        logger.info('Looking for h5 files...')
        files = locate_roots('*.h5', directory)
        logger.info('Found %s h5 files.' % len(files))
                
        summary = tc_open_for_writing(my_summary_file)
        
        if files:    
            pb = progress_bar('Opening files', len(files))
            for i, file in enumerate(files):
                pb.update(i)
                # do not consider the index itself
                if os.path.basename(file).startswith('index'):
                    continue
                
                # print "Trying to open %s" % file
                f = tc_open_for_reading(file)
        
                if not FLYDRA_ROOT in f.root:
                    print 'Ignoring file %s: no data belonging to Flydra DB' % \
                        os.path.basename(file)
                    tc_close(f)
                    continue
                
                link_everything(src=f, dst=summary,
                                src_filename=os.path.basename(file),
                                dst_directory=directory)
             
                tc_close(f)
                        
        # make sure we have the skeleton
        # even though there's no data
        if not 'flydra' in summary.root:
            summary.createGroup('/', 'flydra')
        if not 'samples' in summary.root.flydra:
            summary.createGroup('/flydra', 'samples')
            
        tc_close(summary)
        
        # now copy the temp_file to the main one
        shutil.copyfile(my_summary_file, summary_file)
        
    else:
        # if the index already exists, create a private copy
        shutil.copyfile(summary_file, my_summary_file)
    
    # (re) open the private copy
    return tc_open_for_appending(my_summary_file)
        
        
def link_everything(src, dst, src_filename, dst_directory):
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
                relname = os.path.relpath(src.filename, dst_directory)
                url = "%s:%s" % (relname, table._v_pathname)
                target = url
                # target = table
                dst.createExternalLink(parent, child,
                                       target, warn16incompat=False)


    
    
    
    
