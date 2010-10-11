from geometric_saccade_detector.filesystem_utils import locate_roots
import tables
import os

FLYDRA_ROOT = 'flydra'

class FlydraDB:
    
    def __init__(self, directory):
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
    
    def set_rows(self, id, rows):
        sample_group = self.get_sample_group(id)
        filename = os.path.join(self.directory, id + '.h5')
        f = tables.openFile(filename, 'w')
        filters = tables.Filters(complevel=1, complib='zlib', fletcher32=True)
        rows_table = f.createTable(sample_group._v_pathname, 'rows',
                                   rows, createparents=True, filters=filters)
        self.index.createExternalLink(sample_group, 'rows',
                                      rows_table, warn16incompat=False)
        f.close()
        
    def has_rows(self, id):
        assert self.has_sample(id)
        group = self.get_sample_group(id)
        
        return 'rows' in group
        
    def get_rows(self, id):
        ''' Get the trajectory data for a certain sample. '''
        assert self.has_rows(id)    
        ref = self.get_sample_group(id).rows
        return ref(mode='a') # dereference
    
    def list_images(self, id):
        ''' Returns the images computed for sample. '''
        assert self.has_sample(id)
        sample_group = self.get_sample_group(id)
        if not 'images' in sample_group:
            self.index.createGroup(sample_group, 'images') 
        return list(sample_group.images._v_children)

    def has_image(self, id, image):
        ''' Checks that an image is computed for a certain sample. '''
        return image in self.list_images(id)
    
    def get_image(self, id, image):
        ''' Get a reference to the image table for a certain sample. 
            The table is created if not present. '''
        assert self.has_image(id, image)
        ref = self.get_sample_group(id).images._f_getChild(image)  
        return ref(mode='a') # dereference
        
    def add_image(self, id, image, value):
        assert self.has_sample(id)

        sample_group = self.get_sample_group(id)
        images = sample_group.images
        # remove if present
        if image in images:
            images._f_getChild(image)._f_remove()
        
        filename = os.path.join(self.directory, id + '-%s.h5' % image)
        
        f = tables.openFile(filename, 'w')
        filters = tables.Filters(complevel=1, complib='zlib', fletcher32=True)
        value_table = f.createTable(images._v_pathname, image,
                                   value, createparents=True, filters=filters)
        
            
        self.index.createExternalLink(images, image,
                                      value_table, warn16incompat=False)
        f.close()
    
        
    def close(self):
        self.index.close()



def db_summary(directory):
    files = locate_roots('*.h5', directory)
    summary_file = os.path.join(directory, 'index.h5')
    summary = tables.openFile(summary_file, 'w')
    for file in files:
        # do not consider the index itself
        if os.path.samefile(file, summary_file):
            continue
        
        f = tables.openFile(file, 'r')

        if not FLYDRA_ROOT in f.root:
            print 'Ignoring file %s' % os.path.basename(file)
            continue
        
        link_everything(src=f, dst=summary, src_filename=os.path.basename(file))
        
        f.close()
    
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
                dst.createExternalLink(parent, child, table, warn16incompat=False)


    
    
    
    
