import sys, numpy
from optparse import OptionParser

from flydra_render import logger
from flydra_render.db import FlydraDB
from flydra_render.progress import progress_bar
from flydra_render.main_render import get_rfsee_client

description = """

Usage: ::

    $ flydra_render_saccades --db <flydra db>  [--white] [--nocache]

This program iterates over the ``saccades`` table, and renders the scene 
at the beginning and end of the saccade.

Two tables are created:

- ``saccades_view_start_luminance``: view at the beginning of the 
  saccade, given by the field ``orientation_start``.
  
- ``saccades_view_stop_luminance``: view at the end of the saccade, 
  given by the field ``orientation_stop``.
  
Each of these tables is as big as the saccades table.

If ``--white`` is specified, the arena walls are displayed in white. 
In this case, the tables are named ``saccades_view_start_luminance_w`` 
and ``saccades_view_stop_luminance_w``.

The ``--host`` option allows you to use a remote fsee instance.
See the documentation for ``flydra_render`` for details.

"""

def main():
    
    parser = OptionParser(usage=description)

    parser.add_option("--db", default='flydra_render_output',
                      help="Data directory")

    parser.add_option("--nocache", help="Ignores already computed results.",
                      default=False, action="store_true")
    
    parser.add_option("--white", help="Computes luminance_w, with the arena"
                      " painted white.", default=False, action="store_true")
    
    parser.add_option("--host", help="Use a remote rfsee. Otherwise," 
                      "use local process.", default=None)
    
    (options, args) = parser.parse_args()
    

    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)
        
        
    db = FlydraDB(options.db)
    
    if args:
        do_samples = args
        
    else:
        # look for samples with the rows table
        all_samples = db.list_samples()
        do_samples = filter(lambda x: db.has_saccades(x) and 
                                      db.has_attr(x, 'stimulus_xml'),
                            all_samples)
        logger.info('Found %d/%d samples with saccades and stimulus info.' % 
                    (len(do_samples), len(all_samples)))
    
    if options.white:
        target_start = 'saccades_view_start_luminance_w'
        target_stop = 'saccades_view_stop_luminance_w'
    else:
        target_start = 'saccades_view_start_luminance'
        target_stop = 'saccades_view_stop_luminance'
    
    for i, sample_id in enumerate(do_samples):
        
        logger.info('Sample %s/%s: %s' % (i + 1, len(do_samples), sample_id))
        
        if not db.has_sample(sample_id):
            raise Exception('Sample %s not found in db.' % sample_id)
        
        if not db.has_saccades(sample_id):
            raise Exception('Sample %s does not have saccades table.' % sample_id)
        
        if not db.has_attr(sample_id, 'stimulus_xml'):
            raise Exception('Sample %s does not have the stimulus'
                            ' information ("stimulus_xml")' % sample_id)
       
        # todo: check stale dependencies
        if db.has_table(sample_id, target_start) and \
            db.has_table(sample_id, target_stop) and not options.nocache:
            logger.info('Targets already computed for %s; skipping' % sample_id)
            continue
        
        # Get the stimulus description
        stimulus_xml = db.get_attr(sample_id, 'stimulus_xml')
        saccades = db.get_saccades(sample_id)
        
        view_start, view_stop = render_saccades_view(
            saccades=saccades,
            stimulus_xml=stimulus_xml,
            host=options.host,
            white=options.white)
   
        db.set_table(sample_id, target_start, view_start)
        db.set_table(sample_id, target_stop, view_stop)
         
   
def render_saccades_view(saccades, stimulus_xml, host=None, white=False):
   
    client = get_rfsee_client(host)
        
    if white: # before stimulus_xml
        client.config_use_white_arena()
        
    client.config_stimulus_xml(stimulus_xml)    
    

    num_frames = len(saccades)
    dtype = [('time', 'float64'),
             ('obj_id', 'int'),
             ('frame', 'int'),
             ('value', ('float32', 1398))]
    view_start = numpy.zeros(shape=(num_frames,), dtype=dtype)
    view_stop = numpy.zeros(shape=(num_frames,), dtype=dtype)
     
    
    pb = progress_bar('Rendering saccades', num_frames)
    
    for i in range(num_frames):
        pb.update(i)
        
        saccade = saccades[i]
        orientation_start = numpy.radians(saccade['orientation_start'])
        orientation_stop = numpy.radians(saccade['orientation_stop'])
        
        position = saccade['position']
        attitude_start = rotz(orientation_start)
        attitude_stop = rotz(orientation_stop)
        linear_velocity_body = [0, 0, 0]
        angular_velocity_body = [0, 0, 0]
        
        res_start = client.render(position, attitude_start,
                                  linear_velocity_body,
                                  angular_velocity_body)
        res_stop = client.render(position, attitude_stop,
                                  linear_velocity_body,
                                  angular_velocity_body)
        
        view_start['value'][i] = numpy.array(res_start['luminance'])
        view_stop['value'][i] = numpy.array(res_stop['luminance'])
        
        # copy other frames
        view_start['frame'][i] = saccades[i]['frame']
        view_stop['frame'][i] = saccades[i]['frame']
        view_start['obj_id'][i] = saccades[i]['obj_id']
        view_stop['obj_id'][i] = saccades[i]['obj_id']
        view_start['time'][i] = saccades[i]['time_middle']
        view_stop['time'][i] = saccades[i]['time_middle']
        
    
    client.close()

    return view_start, view_stop

def rotz(theta):
    return numpy.array([ 
            [ +numpy.cos(theta), -numpy.sin(theta), 0],
            [ +numpy.sin(theta), +numpy.cos(theta), 0],
            [0, 0, 1]]) 


if __name__ == '__main__':
    main()
