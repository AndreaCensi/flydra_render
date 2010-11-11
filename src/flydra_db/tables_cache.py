import os
import tables

class OpenFile(object):
    def __init__(self, pytables_handle):
        self.pytables_handle = pytables_handle
        self.num_references = 1

    open_files = {}

def tc_open_for_reading(filename):
    filename = os.path.realpath(filename)
    
    if filename in OpenFile.open_files:
        open = OpenFile.open_files[filename] 
        open.num_references += 1
        # print "tc: reused %s r (%s total) " % (filename, len(OpenFile.open_files))
        return open.pytables_handle
    else: 
        f = tables.openFile(filename, 'r')
        OpenFile.open_files[filename] = OpenFile(f)
        # print "tc: opened %s r (%s total) " % (filename, len(OpenFile.open_files))
        return f

def tc_open_for_writing(filename):
    ''' Throws exception if it is already open. '''
    filename = os.path.realpath(filename)

    if filename in OpenFile.open_files:
        raise Exception('File "%s" already open, '
                        'cannot open again for writing.' % filename)
    else: 
        f = tables.openFile(filename, 'w')
        OpenFile.open_files[filename] = OpenFile(f)
        
        # print "tc: opened %s w (%s total) " % (filename, len(OpenFile.open_files))
        return f


def tc_open_for_appending(filename):
    ''' Throws exception if it is already open. '''
    filename = os.path.realpath(filename)

    if filename in OpenFile.open_files:
        raise Exception('File "%s" already open, '
                        'cannot open again for writing.' % filename)
    else: 
        f = tables.openFile(filename, 'r+')
        OpenFile.open_files[filename] = OpenFile(f)
        
        # print "tc: opened %s w (%s total) " % (filename, len(OpenFile.open_files))
        return f

    
def tc_close(handle):
    ''' Decreases the reference counting and closes the file if
        it is the last one. '''
    if isinstance(handle, str):
        filename = handle
        filename = os.path.realpath(filename)
    else:
        assert isinstance(handle, tables.file.File)
        filename = handle.filename
        
    open = OpenFile.open_files[filename]
    open.num_references -= 1
    
    if open.num_references == 0:
        open.pytables_handle.close()
        del OpenFile.open_files[filename]
         
