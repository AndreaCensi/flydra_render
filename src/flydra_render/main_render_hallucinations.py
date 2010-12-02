import numpy
from collections import namedtuple
from optparse import OptionParser

from flydra_db import FlydraDB
 
from . import logger
from .main_render import render


StimulusStats = namedtuple('StimulusStats', 'stimulus stimulus_xml probability total_number total_length')

def get_db_stimulus_stats(db, include_nopost=False):
    """
        Returns a list of tuple (stimulus, stimulus_xml, probability, number of logs, total length)
        describing the distribution of stimuli, excluding nopost
    
        db
          FlydraDB instance.
    
    """

    # flydra XML 
    stimulus2xml = {}
    # number of logs
    stimulus2count = {}
    # length of logs
    stimulus2length = {}

    for sample in db.list_samples():
        if db.has_attr(sample, 'stimulus'):
            stimulus = db.get_attr(sample, 'stimulus')
            if stimulus == 'nopost' and not include_nopost:
                continue
            
            stimulus2xml[stimulus] = db.get_attr(sample, 'stimulus_xml')
            
            if not stimulus in stimulus2count:
                stimulus2count[stimulus] = 0
                stimulus2length[stimulus] = 0
                
            stimulus2count[stimulus] += 1
            
            rows = db.get_table(sample, 'rows')
            stimulus2length[stimulus] += len(rows)
            db.release_table(rows)
             
    print stimulus2count
    
    n = sum(stimulus2count.values())
    
    for stimulus in stimulus2xml:
        probability = stimulus2count[stimulus] * 1.0 / n
        yield StimulusStats(stimulus=stimulus, stimulus_xml=stimulus2xml[stimulus],
                        probability=probability, total_number= stimulus2count[stimulus],
                        total_length=stimulus2length[stimulus])

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
        for k in range(int(num)): #@UnusedVariable
            yield i
    
        
def get_stimulus_to_use(db, n):
    ''' Returns a list of n tuples (stimulus, stimulus_xml) representing
        a representative sample of the stimuli present in the logs with posts.
    '''

    stats = list(get_db_stimulus_stats(db))
    # fIXME: check again
    for s in stats: #@UnusedVariable
        print "stimulus %s  %.3f" % (s.stimulus, s.probability)
  
    # get probability distribution
    pd = map(lambda x: s.probability, stats)
    
    stimulus_for_sample_index = list(get_sample_for_distribution(pd, n))
   
    for i in stimulus_for_sample_index:
        yield stats[i].stimulus, stats[i].stimulus_xml
        
        
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
        
    print "Summary, including nopost."
    for s in sorted( get_db_stimulus_stats(db, include_nopost=True), 
                       key=(lambda x: -x.total_length) ):
        print "stimulus: {s.stimulus:>10}  samples: {s.total_number:>5}  "\
              " total length: {len:>5} minutes".format(s=s, len=s.total_length / (60 * 60))
        
    
      
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
