import shutil, fnmatch, os, tempfile

from .tables_cache import tc_open_for_writing, tc_open_for_reading, \
    tc_open_for_appending, tc_close
from .progress import progress_bar
from .log import logger
from .constants import FLYDRA_ROOT


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
    my_summary = tempfile.NamedTemporaryFile(suffix='.h5_priv',
                                             prefix='.index', dir=temp_dir)
    my_summary_file = my_summary.name
 
    # if it does not exist or it is updated, recreate it 
    if not os.path.exists(summary_file) or \
        os.path.getmtime(directory) > os.path.getmtime(summary_file):
    
        logger.info('Summary file %s out of date or not existing; recreating.' % \
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
                                #src_filename=os.path.basename(file),
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
        
        
def link_everything(src, dst, dst_directory):
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

def locate_roots(pattern, where):
    "where: list of files or directories where to look for pattern"
    if not(type(where) == list):
        where = [where];

    all_files = []
    for w in where:
        if not(os.path.exists(w)):
            raise ValueError, "Path %s does not exist" % w
        if os.path.isfile(w):
            all_files.append(w)
        elif os.path.isdir(w):
            all_files.extend(set(locate(pattern=pattern, root=w)))

    return all_files


def locate(pattern, root):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''
    for path, dirs, files in os.walk(os.path.abspath(root)): #@UnusedVariable
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)
            
