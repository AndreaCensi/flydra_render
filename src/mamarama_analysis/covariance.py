from flydra_render.db import FlydraDB
def compute_image_mean(db, samples, image):
    ''' 
    db: FlydraDB directory
    samples: list of IDs
    '''
    
    db = FlydraDB(db)
    
    mean = None
    num = None
    
    for id in samples:
        if not (db.has_sample(id) and db.has_image(id, image)):
            raise ValueError('Not enough data for id %s' % id)
        
        data = db.get_image(id, image)
        
        values = data[:]['value']
        
        sample_mean = values.mean(axis=0)
        sample_num = len(data)
        
        if mean is None:
            num = sample_num
            mean = sample_mean
        else:
            mean = (mean * num + sample_mean * sample_num) / (sample_num + num)
            num = sample_num + num
            
    return mean
            
            
            
        
        
    
