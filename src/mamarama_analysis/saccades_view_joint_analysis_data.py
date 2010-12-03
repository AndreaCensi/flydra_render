import numpy

from compmake import progress

# XXX: remove dependency
from saccade_analysis.tammero.tammero_analysis import add_position_information

def saccades_iterate_image(name, db, samples, image, conditions):
    ''' Iterates over the values of an image corresponding to
        the saccades that respect a given condition.
        
        yields  sample, saccades, image_values 
    '''
    
    num_saccades = 0
    num_selected = 0
    for i, id in enumerate(samples):
        progress(name, (i, len(samples)), "Sample %s" % id)
    
        if not db.has_saccades(id):
            raise ValueError('No saccades for %s' % id)
        if not (db.has_sample(id) and db.has_table(id, image)):
            raise ValueError('No table "%s" for id %s' % (image, id))
        
        saccades_table = db.get_saccades(id)
        
        saccades = add_position_information(saccades_table)
        
        data = db.get_table(id, image)
        
        # computes and of all conditions
        select = reduce(numpy.logical_and,
                        map(lambda c:c(saccades), conditions))
        
        values = data[select]['value']
        
        if len(values) == 0:
            print ("No saccades selected for %s (out of %d)." % 
                   (id, len(saccades)))
        else:
            yield id, saccades[select], values
        
        num_saccades += len(select)
        num_selected += (select * 1).sum()
        db.release_table(data)
        db.release_table(saccades_table)
    ratio = 100.0 / num_saccades * num_selected
    print "Selected %.2f %% of saccades" % ratio
