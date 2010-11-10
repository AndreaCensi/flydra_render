
from optparse import OptionParser
 
from flydra_render import logger
from flydra_render.db import FlydraDB 
import numpy
from flydra_render.main_render import render

def get_db_stimulus_stats(db):
    """
        Returns a list of tuple (stimulus, stimulus_xml, probability)
        describing the distribution of stimuli, excluding nopost
    
        db
          FlydraDB instance.
    
    """

    stimulus2xml = {}
    stimulus2count = {}

    for sample in db.list_samples():
        if db.has_attr(sample, 'stimulus'):
            stimulus = db.get_attr(sample, 'stimulus')
            if stimulus == 'nopost':
                continue
            
            stimulus2xml[stimulus] = db.get_attr(sample, 'stimulus_xml')
            
            if not stimulus in stimulus2count:
                stimulus2count[stimulus] = 0
                
            stimulus2count[stimulus] += 1
             
    print stimulus2count
    
    n = sum(stimulus2count.values())
    
    for stimulus in stimulus2xml:
        yield stimulus, stimulus2xml[stimulus], stimulus2count[stimulus] * 1.0 / n

def get_sample_for_distribution(pd, n):
    ''' pd: list of numbers describing a discrete distribution.
         n: number of samples to extract. 
         returns a list of n number
    '''
    
    # Idea: err on the side of caution
    # sort the probabilities least 
    pd = numpy.array(pd)
    
    approx = numpy.ceil(pd * n)
    
    toomany = int(approx.sum() - n)
    
    # remove some from the 
    # print pd
    # print approx
    # print toomany
    
    largest = numpy.argsort(-approx)
    for i in range(toomany):
        index = largest[i % len(largest)]
        approx[index] -= 1
    
    # print approx
    
    assert approx.sum() == n

    for i, num in enumerate(approx):
        for k in range(int(num)):
            yield i
    
        
def get_stimulus_to_use(db, n):
    ''' Returns a list of n tuples (stimulus, stimulus_xml) representing
        a representative sample of the stimuli present in the logs with posts.
    '''

    stats = list(get_db_stimulus_stats(db))
    for stimulus, xml, probability in stats: #@UnusedVariable
        print "stimulus %s  %.3f" % (stimulus, probability)
  
    # get probability distribution
    pd = map(lambda x: x[2], stats)
    
    stimulus_for_sample_index = list(get_sample_for_distribution(pd, n))
   

    for i in stimulus_for_sample_index:
        stimulus =    stats[i][0]
        stimulus_xml =  stats[i][1]
        yield stimulus, stimulus_xml
        
        
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
    
    (options, args) = parser.parse_args() #@UnusedVariable
     
        
    db = FlydraDB(options.db, False)
    
        
    # look for samples with the rows table
    do_samples = db.list_samples()
    do_samples = filter(lambda x: db.has_rows(x) and 
                        db.get_attr(x, 'stimulus') == 'nopost',
                        do_samples)
    if not do_samples:
        raise Exception('Cannot find samples to hallucinate about.')
      
    stimulus_to_use = list(get_stimulus_to_use(db, len(do_samples)))
    
    for i, sample in enumerate(do_samples):
        stimulus = stimulus_to_use[i][0]
        print sample, stimulus 
    
    if options.white:
        target = 'hluminance_w'
    else:
        target = 'hluminance'
    
    for i, sample_id in enumerate(do_samples):
        stimulus = stimulus_to_use[i][0]
        stimulus_xml = stimulus_to_use[i][1]
            
        print 'Sample %s/%s: %s' % (i + 1, len(do_samples), sample_id)
        
        if not db.has_sample(sample_id):
            raise Exception('Sample %s not found in db.' % sample_id)
        
        if not db.has_rows(sample_id):
            raise Exception('Sample %s does not have rows table.' % sample_id)
         
        if options.compute_mu:
            if db.has_table(sample_id, 'nearness') and not options.nocache:
                logger.info('Already computed nearness for %s; skipping' % sample_id)
                continue
        else:
            if db.has_table(sample_id, target) and not options.nocache:
                logger.info('Already computed luminance for %s; skipping' % sample_id)
                continue
        
        rows = db.get_rows(sample_id)
        
         
        results = render(rows, stimulus_xml, host=options.host,
                         compute_mu=options.compute_mu, white=options.white)
   
        db.set_table(sample_id, target, results['luminance'])
        
        if options.compute_mu:
            db.set_table(sample_id, 'hnearness', results['nearness'])
            db.set_table(sample_id, 'hretinal_velocities',
                         results['retinal_velocities'])
        
        db.release_table(rows)    
    
    db.close()

if __name__ == '__main__':
    main()
