from procgraph import Block, Generator
from flydra_db import FlydraDB


class FlydraImage(Generator):
    ''' This block outputs the retinal images from a FlydraDB for 
        a particular sample. '''
    Block.alias('flydra_db_image')
        
    Block.config('db', 'Database directory')
    Block.config('sample', 'Sample ID -- such as "DATA20080611_191809".')
    Block.config('image', 'Which retinal image to display.')
    
    Block.output('obj_id')
    Block.output('frame')
    Block.output('image')
    
    def init(self):
        self.db = FlydraDB(self.config.db)
        if not self.db.has_sample(self.config.sample):
            raise ValueError('Sample "%s" not found.' % self.config.sample)
        if not self.db.has_table(self.config.sample, self.config.image):
            raise ValueError('Table "%s" not found for sample %s.' %\
                    (self.config.image,self.config.sample))

        self.data = self.db.get_table(self.config.sample, self.config.image)
        
        self.next_index = 0
        if len(self.data) == 0:
            self.info('Empty rows for sample %s.' % self.config.sample)
            self.next_index = None

    def update(self):
        row = self.data[self.next_index]
        t = row['time']
        
        for field in ['obj_id', 'frame']:
            self.set_output(field, value=row[field], timestamp=t)
        
        self.set_output('image', row['value'], timestamp=t)
        
        self.next_index += 1
        if self.next_index == len(self.data):
            self.next_index = None
        
    def next_data_status(self):
        # TODO: put new interface
        if self.next_index is None: # EOF
            return (False, None)
        else:
            return (True, self.data[self.next_index]['time'])
