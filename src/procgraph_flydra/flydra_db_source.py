from procgraph import Block, Generator 
from flydra_db  import FlydraDB

fields = [
     'obj_id',
     'frame',
     'position',
     'attitude',
     
     'linear_velocity_body',
     'linear_velocity_world',
     'linear_velocity_modulus',
     
     'linear_acceleration_body',
     'linear_acceleration_world',
     'linear_acceleration_modulus',
     
     'angular_velocity_body',
     'angular_velocity_world',
     
     'reduced_angular_orientation',
     'reduced_angular_velocity',
     'reduced_angular_acceleration']

class FlydraData(Generator):
    ''' This block outputs the data from a FlydraDB for 
        a particular sample. '''
    Block.alias('flydra_db_source')
        
    Block.config('db', 'Database directory')
    Block.config('sample', 'Sample ID -- such as "DATA20080611_191809".')
    
    for f in fields:
        Block.output(f)
    
    Block.output('stimulus_xml')
    
    def init(self):
        self.db = FlydraDB(self.config.db, False)
        self.rows = self.db.get_rows(self.config.sample)
        self.next_index = 0

    def update(self):
        row = self.rows[self.next_index]
        t = row['time']
        
        for field in fields:
            self.set_output(field, value=row[field].copy(), timestamp=t)
        
        if self.db.has_attr(self.config.sample, 'stimulus_xml'):
            stim_xml = self.db.get_attr(self.config.sample, 'stimulus_xml')
            self.set_output('stimulus_xml', stim_xml, timestamp=t)
        
        self.next_index += 1
        if self.next_index == len(self.rows):
            self.next_index = None
        
    def next_data_status(self):
        # TODO: put new interface
        if self.next_index is None: # EOF
            return (False, None)
        else:
            return (True, self.rows[self.next_index]['time'])

    
