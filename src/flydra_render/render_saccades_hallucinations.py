import sys, numpy
from optparse import OptionParser

from flydra_render import logger
from flydra_render.db import FlydraDB
from flydra_render.progress import progress_bar
from flydra_render.main_render import get_rfsee_client

description = """

Usage: ::

    $ flydra_render_saccades --db <flydra db>  [--white] [--nocache] [IDs]

This program iterates over the ``saccades`` table, and renders the scene 
at the beginning and end of the saccade.

Four tables are created:

- ``saccades_view_start_luminance``: view at the beginning of the 
  saccade, given by the field ``orientation_start``.
  
- ``saccades_view_stop_luminance``: view at the end of the saccade, 
  given by the field ``orientation_stop``.
  
- ``saccades_view_rstop_luminance``: view according to data sample 

- ``saccades_view_random_luminance``: view according to random position


  
Each of these tables is as big as the saccades table.

If ``--white`` is specified, the arena walls are displayed in white. 
In this case, the tables are named ``saccades_view_start_luminance_w``,
``saccades_view_stop_luminance_w``

The ``--host`` option allows you to use a remote fsee instance.
See the documentation for ``flydra_render`` for details.

"""

def main():
    
    parser = OptionParser(usage=description)

    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

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
    
    image = 'luminance_w' if options.white else 'luminance'
        
    target_start = 'saccades_view_start_%s' % image
    target_stop = 'saccades_view_stop_%s' % image
    target_rstop = 'saccades_view_rstop_%s' % image
    target_random = 'saccades_view_random_%s' % image
    
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
            db.has_table(sample_id, target_stop) and \
            db.has_table(sample_id, target_rstop) and \
            db.has_table(sample_id, target_random) and \
            not options.nocache:
            logger.info('Targets already computed for %s; skipping' % sample_id)
            continue
        
        # Get the stimulus description
        stimulus_xml = db.get_attr(sample_id, 'stimulus_xml')
        saccades = db.get_saccades(sample_id)
        
        view_start, view_stop, view_rstop, view_random = render_saccades_view(
            saccades=saccades,
            stimulus_xml=stimulus_xml,
            host=options.host,
            white=options.white)
   
        db.set_table(sample_id, target_start, view_start)
        db.set_table(sample_id, target_stop, view_stop)
        db.set_table(sample_id, target_rstop, view_rstop)
        db.set_table(sample_id, target_random, view_random)
         
   
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
    view_rstop = numpy.zeros(shape=(num_frames,), dtype=dtype)
    view_random = numpy.zeros(shape=(num_frames,), dtype=dtype)
    
    pb = progress_bar('Rendering saccades', num_frames)
    
    for i in range(num_frames):
        pb.update(i)
        
        saccade = saccades[i]
        orientation_start = numpy.radians(saccade['orientation_start'])
        orientation_stop = numpy.radians(saccade['orientation_stop'])
        
        # simulate how it would look like sampling from a random distribution
        random_index = numpy.random.randint(0, len(saccades))
        random_displacement = \
            numpy.radians(saccades[random_index]['amplitude']) * \
            saccades[random_index]['sign']
        orientation_rstop = orientation_start + random_displacement
        
        # finally, a random orientation
        orientation_random = numpy.random.rand() * 2 * numpy.pi
        
        position = saccade['position']
        attitude_start = rotz(orientation_start)
        attitude_stop = rotz(orientation_stop)
        attitude_rstop = rotz(orientation_rstop)
        attitude_random = rotz(orientation_random)
        
        
        linear_velocity_body = [0, 0, 0]
        angular_velocity_body = [0, 0, 0]
        
        res_start = client.render(position, attitude_start,
                                  linear_velocity_body,
                                  angular_velocity_body)
        res_stop = client.render(position, attitude_stop,
                                  linear_velocity_body,
                                  angular_velocity_body)
        res_rstop = client.render(position, attitude_rstop,
                                  linear_velocity_body,
                                  angular_velocity_body)
        res_random = client.render(position, attitude_random,
                                  linear_velocity_body,
                                  angular_velocity_body)
        
        view_start['value'][i] = numpy.array(res_start['luminance'])
        view_stop['value'][i] = numpy.array(res_stop['luminance'])
        view_rstop['value'][i] = numpy.array(res_rstop['luminance'])
        view_random['value'][i] = numpy.array(res_random['luminance'])
        
        # copy other fields
        for arr in [view_start, view_stop, view_rstop, view_random]:
            arr['frame'][i] = saccades[i]['frame']
            arr['obj_id'][i] = saccades[i]['obj_id']
            arr['time'][i] = saccades[i]['time_middle']
             
    
    client.close()

    return view_start, view_stop, view_rstop, view_random

def rotz(theta):
    return numpy.array([ 
            [ +numpy.cos(theta), -numpy.sin(theta), 0],
            [ +numpy.sin(theta), +numpy.cos(theta), 0],
            [0, 0, 1]]) 


if __name__ == '__main__':
    main()
