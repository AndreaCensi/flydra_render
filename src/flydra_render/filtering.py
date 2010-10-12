from geometric_saccade_detector.math_utils import merge_fields
import numpy
from numpy.testing.utils import assert_almost_equal
from flydra_render.structures import additional_fields




def normalize(v):
    ''' Normalizes a vector by its length. '''
    return v / numpy.linalg.norm(v)


def filter_rows(rows, options):
    
    attitude_algo = 'ROLL0PITCH0'
    
    extra = numpy.ndarray(dtype=additional_fields, shape=rows.shape)
    
    minimum_linear_velocity = 0.02
    
    x = rows['x']
    y = rows['y']
    z = rows['z']
    xvel = rows['xvel']
    yvel = rows['yvel']
    zvel = rows['zvel']
    
    position = extra['position']
    attitude = extra['attitude']
    linear_velocity_world = extra['linear_velocity_world']
    reduced_angular_orientation = extra['reduced_angular_orientation']
    linear_velocity_modulus = extra['linear_velocity_modulus']
    linear_velocity_body = extra['linear_velocity_body']
    angular_velocity_body = extra['angular_velocity_body']
    
    extra['time'] = (rows['frame'] - rows['frame'][0]) / 60.0
       
    for i in xrange(len(extra)):
        position[i] = numpy.array([x[i], y[i], z[i]])
        linear_velocity_world[i] = numpy.array([xvel[i], yvel[i], zvel[i]])
        linear_velocity_modulus[i] = numpy.linalg.norm(linear_velocity_world[i]) 

        if attitude_algo == 'ROLL0PITCH0':
            # assume roll = 0, pitch = 0
            if linear_velocity_modulus[i] > minimum_linear_velocity:
                x_axis = normalize(numpy.array(
                    [linear_velocity_world[i][0],
                     linear_velocity_world[i][1],
                     0]))
                up = numpy.array([0, 0, 1])
                y_axis = normalize(numpy.cross(up, x_axis))
                z_axis = normalize(numpy.cross(x_axis, y_axis));
                R = numpy.eye(3);
                R[:, 0] = x_axis
                R[:, 1] = y_axis
                R[:, 2] = z_axis
                attitude[i] = R;
                #print linear_velocity_world[i]
                #print R
                assert_almost_equal(numpy.linalg.det(R), 1)
            else:
                if i > 0:
                    attitude[i] = attitude[i - 1]
                else:
                    attitude[i] = numpy.eye(3)
        else:
            raise Exception('Uknown attitude algo "%s".' % attitude_algo)
        
        front = numpy.dot(attitude[i], [1, 0, 0])
        reduced_angular_orientation[i] = numpy.arctan2(front[1], front[0])

                
        
        linear_velocity_body[i] = numpy.dot(attitude[i].T, linear_velocity_world[i]);
        angular_velocity_body[i] = 0

 
    return merge_fields(rows, extra)



        

