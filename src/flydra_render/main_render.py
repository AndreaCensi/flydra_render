from optparse import OptionParser
from flydra_render import logger
import sys
from flydra_render.db import FlydraDB
from rfsee.rfsee_client import ClientTCP
import numpy
from flydra_render.progress import progress_bar

def main():
    
    parser = OptionParser()

    parser.add_option("--db", default='flydra_render_output',
                      help="Data directory")

    parser.add_option("--nocache", help="Ignores already computed results.",
                      default=False, action="store_true")

    parser.add_option("--compute_mu", help="Computes mu and optic flow.",
                      default=False, action="store_true")


    
    
    (options, args) = parser.parse_args()
    

    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)
        
        
    db = FlydraDB(options.db)
    
    if args:
        do_samples = args
    else:
        do_samples = db.list_samples()
    
    for i, sample_id in enumerate(do_samples):
        
        print 'Sample %s/%s: %s' % (i + 1, len(do_samples), sample_id)
        
        if not db.has_sample(sample_id) or not db.has_rows(sample_id):
            raise Exception('Sample %s not found in db.' % sample_id)
        
        if options.compute_mu:
            if db.has_image(sample_id, 'nearness') and not options.nocache:
                print 'Already computed nearness for %s; skipping' % sample_id
                continue
        else:
            if db.has_image(sample_id, 'luminance') and not options.nocache:
                print 'Already computed luminance for %s; skipping' % sample_id
                continue
        
        rows = db.get_rows(sample_id)
        stimulus_xml = rows._v_attrs.stimulus_xml
        
        results = render(rows, stimulus_xml, compute_mu=options.compute_mu)
   
        db.add_image(sample_id, 'luminance', results['luminance'])
        
        if options.compute_mu:
            db.add_image(sample_id, 'nearness', results['nearness'])
            db.add_image(sample_id, 'retinal_velocities',
                         results['retinal_velocities'])
            
   
def render(rows, stimulus_xml, compute_mu=False,
           host='tokyo', do_distance=False):     
    cp = ClientTCP(host, port=10781)
    cp.config_stimulus_xml(stimulus_xml)    
    cp.config_compute_mu(compute_mu)

    num_frames = len(rows)
    dtype = [('time', 'float64'),
             ('obj_id', 'int'),
             ('frame', 'int'),
             ('value', ('float32', 1398))]
    luminance = numpy.zeros(shape=(num_frames,), dtype=dtype)
    
    # copy index fields
    copy_fields = ['time', 'frame', 'obj_id'] 
    for field in copy_fields: 
        luminance[field] = rows[:][field]
    
    if compute_mu:
        nearness = numpy.zeros(shape=(num_frames,), dtype=dtype)
        dtype = [('time', 'float64'),
                 ('obj_id', 'int'),
             ('frame', 'int'),
             ('value', ('float32', (1398, 2)))]
        retinal_velocities = numpy.zeros(shape=(num_frames,), dtype=dtype)
        
        for a in [nearness, retinal_velocities]:
            for field in copy_fields:
                a[field] = rows[:][field]
     
    #num_frames = 20
    
    pb = progress_bar('Rendering', num_frames)
    
    for i in range(num_frames):
        pb.update(i)
        
        position = rows[i]['position']
        attitude = rows[i]['attitude']
        linear_velocity_body = rows[i]['linear_velocity_body']
        angular_velocity_body = rows[i]['angular_velocity_body']
        
        def simple(x):
            return [x[0], x[1], x[2]]
        
        def simple_matrix(x):
            return [ [ x[0, 0], x[0, 1], x[0, 2]],
                     [ x[1, 0], x[1, 1], x[1, 2]],
                     [ x[2, 0], x[2, 1], x[2, 2]]  ]
                     
        res = cp.render(simple(position), simple_matrix(attitude),
            simple(linear_velocity_body), simple(angular_velocity_body))

        
        luminance['value'][i] = numpy.array(res['luminance'])
        
        if compute_mu:
            nearness['value'][i] = numpy.array(res['nearness'])
            retinal_velocities['value'][i] = numpy.array(res['retinal_velocities'])
    
    res = {'luminance': luminance}
    if compute_mu:
        res['retinal_velocities'] = retinal_velocities
        res['nearness'] = nearness
    
    return res
    



if __name__ == '__main__':
    main()
