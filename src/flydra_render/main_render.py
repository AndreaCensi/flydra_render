import sys, numpy
from optparse import OptionParser

from rfsee.rfsee_client import ClientTCP, ClientProcess

from flydra_render import logger
from flydra_render.db import FlydraDB
from flydra_render.progress import progress_bar


def main():
    
    parser = OptionParser()
    
    parser.add_option("--db", default='flydra_db', help="FlydraDB directory")

    parser.add_option("--nocache", help="Ignores already computed results.",
                      default=False, action="store_true")

    parser.add_option("--compute_mu", help="Computes mu and optic flow.",
                      default=False, action="store_true")
    
    parser.add_option("--white", help="Computes luminance_w, with the arena"
                      " painted white.", default=False, action="store_true")
    
    parser.add_option("--host", help="Use a remote rfsee. Otherwise, use local process.",
                       default=None)
    
    (options, args) = parser.parse_args()
    

    if options.db is None:
        logger.error('Please specify a directory using --db.')
        sys.exit(-1)
        
        
    db = FlydraDB(options.db)
    
    if args:
        do_samples = args
    else:
        # look for samples with the rows table
        do_samples = db.list_samples()
        do_samples = filter(lambda x: db.has_rows(x), do_samples)
    
    if options.white:
        target = 'luminance_w'
    else:
        target = 'luminance'
    
    for i, sample_id in enumerate(do_samples):
        
        print 'Sample %s/%s: %s' % (i + 1, len(do_samples), sample_id)
        
        if not db.has_sample(sample_id):
            raise Exception('Sample %s not found in db.' % sample_id)
        if not db.has_rows(sample_id):
            raise Exception('Sample %s does not have rows table.' % sample_id)
       
        if options.compute_mu:
            if db.has_table(sample_id, 'nearness') and not options.nocache:
                print 'Already computed nearness for %s; skipping' % sample_id
                continue
        else:
            if db.has_table(sample_id, target) and not options.nocache:
                print 'Already computed luminance for %s; skipping' % sample_id
                continue
        
        rows = db.get_rows(sample_id)
        stimulus_xml = rows._v_attrs.stimulus_xml
        
        results = render(rows, stimulus_xml, host=options.host,
                         compute_mu=options.compute_mu, white=options.white)
   
        db.set_table(sample_id, target, results['luminance'])
        
        if options.compute_mu:
            db.set_table(sample_id, 'nearness', results['nearness'])
            db.set_table(sample_id, 'retinal_velocities',
                         results['retinal_velocities'])
            
   
def render(rows, stimulus_xml, host=None, compute_mu=False,
           white=False):
    
    cp = get_rfsee_client(host)
    

    if white: # before stimulus_xml
        cp.config_use_white_arena()

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
      
    pb = progress_bar('Rendering', num_frames)
    
    for i in range(num_frames):
        pb.update(i)
        
        position = rows[i]['position']
        attitude = rows[i]['attitude']
        linear_velocity_body = rows[i]['linear_velocity_body']
        angular_velocity_body = rows[i]['angular_velocity_body']
         
        res = cp.render(position, attitude, linear_velocity_body,
                        angular_velocity_body)
        
        luminance['value'][i] = numpy.array(res['luminance'])
        
        if compute_mu:
            nearness['value'][i] = numpy.array(res['nearness'])
            retinal_velocities['value'][i] = numpy.array(res['retinal_velocities'])
    
    res = {'luminance': luminance}
    if compute_mu:
        res['retinal_velocities'] = retinal_velocities
        res['nearness'] = nearness
    
    cp.close()

    return res
    

def get_rfsee_client(host):
    ''' Returns an instance of a rfsee client.
        If host = None, use local process.
        Otherwise, interpret host as "hostname[:port]" for 
        a remote instance. '''
    
    if host is not None:
        tokens = host.split(':')
        if len(tokens) == 2:
            hostname = tokens[0]
            port = tokens[1]
        else:
            hostname = tokens[0]
            port = 10781
            
        client = ClientTCP(hostname, port)
    else:
        client = ClientProcess()
        
    return client

if __name__ == '__main__':
    main()
