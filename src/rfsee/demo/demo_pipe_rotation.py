from rfsee.rfsee_client import ClientProcess
from .example_stimxml import example_stim_xml

# XXX: remove dep
from procgraph_flydra.values2retina import plot_luminance

from reprep import Report

import numpy

def main(): 
    
    cp = ClientProcess()    
    cp.config_stimulus_xml(example_stim_xml)
    position = [0.5, 0.5, 0.5]
    linear_velocity_body = [0, 0, 0]
    angular_velocity_body = [0, 0, 0]
    
    
    r = Report('am-I-crazy-test')
    f = r.figure('varying theta', shape=(3, 3))
    f2 = r.figure('varying x', shape=(3, 3))
    f3 = r.figure('varying y', shape=(3, 3))
    
    desc = lambda position, theta: 'At x: %.2f, y: %.2f, z: %.2f, theta: %d deg' % \
              (position[0], position[1], position[2], numpy.degrees(theta))
    idm = lambda position, theta, t: "%s-x:%.2f,y:%.2f,z:%.2f,th:%.3f" % (t, position[0], position[1], position[2], theta)
        
    for theta in numpy.linspace(0, 2 * numpy.pi, 16):
        position = [0.5, 0.5, 0.5]
        attitude = rotz(theta)
        
        res = cp.render(position, attitude,
                        linear_velocity_body, angular_velocity_body)
        lum = res['luminance']
        id = idm(position, theta, 'theta')
        r.data_rgb(id, plot_luminance(lum))
        f.sub(id, desc(position, theta)) 
              
    for x in numpy.linspace(0, 1, 20):
        position = [x, 0, 0.1]
        theta = 0
        
        res = cp.render(position, attitude,
                        linear_velocity_body, angular_velocity_body)
        id = idm(position, theta, 'x')
        r.data_rgb(id, plot_luminance(res['luminance']))
        f2.sub(id, desc(position, theta))
    
    for y in numpy.linspace(0, 1, 20):
        position = [0, y, 0.1]
        theta = 0
        
        res = cp.render(position, attitude,
                        linear_velocity_body, angular_velocity_body)
        id = idm(position, theta, 'y')
        r.data_rgb(id, plot_luminance(res['luminance']))
        f3.sub(id, desc(position, theta))
    
    
    filename = 'demo_pipe_rotation_experimenting.html'
    print "Writing to %s" % filename
    r.to_html(filename)
    
    cp.close()



def rotz(theta):
    return numpy.array([ 
            [ +numpy.cos(theta), -numpy.sin(theta), 0],
            [ +numpy.sin(theta), +numpy.cos(theta), 0],
            [0, 0, 1]]) 


if __name__ == '__main__':
    main()
