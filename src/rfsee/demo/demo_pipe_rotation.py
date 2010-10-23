from rfsee.rfsee_client import ClientProcess
from rfsee.demo.example_stimxml import example_stim_xml
from procgraph_flydra.values2retina import plot_luminance

from reprep import Report

import numpy

def main(): 
    
    cp = ClientProcess()    
    cp.config_stimulus_xml(example_stim_xml)
    position = [0.5, 0.5, 0.5]
    linear_velocity_body = [0, 0, 0]
    angular_velocity_body = [0, 0, 0]
    
    
    r = Report()
    f = r.figure(shape=(3,3))
    
    orientation = numpy.linspace(0, 2* numpy.pi, 32)
    
    for theta in orientation:
        attitude = rotz(theta)
    
    
        res = cp.render(position, attitude, 
                        linear_velocity_body, angular_velocity_body)
    
        y = res['luminance']
        id  = "%.3f" % theta
        r.data_rgb(id, plot_luminance(y))
        
        f.sub(id, 'At %d deg' % numpy.degrees(theta))
        

    r.to_html('demo_pipe_rotation.html')
    
    cp.close()



def rotz(theta):
    return numpy.array([ 
            [ +numpy.cos(theta), -numpy.sin(theta), 0],
            [ +numpy.sin(theta), +numpy.cos(theta), 0],
            [0, 0, 1]]) 


if __name__ == '__main__':
    main()
