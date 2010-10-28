import numpy
from numpy.testing.utils import assert_almost_equal
from flydra_render.structures import additional_fields
import scipy, scipy.signal
from geometric_saccade_detector.math_utils import normalize_pi
from flydra_render.render_saccades import rotz


def compute_derivative(x, timestamp):
    dt = timestamp[1] - timestamp[0]
    deriv_filter = numpy.array([0.5, 0, -0.5]) / dt
    d = scipy.signal.convolve(x, deriv_filter, mode='same', old_behavior=False) #@UndefinedVariable
    d[0] = d[1]
    d[-1] = d[-2]
    return d        

def merge_fields(a, b):
    ''' Merge the fields of the two numpy arrays a,b. 
        They must have the same shape. '''
    if a.shape != b.shape:    
        raise ValueError('Arrays must have the same shape; '
                         'found %s and %s.' % (str(a.shape), str(b.shape)))
        
    new_dtype = []
    
    for f in a.dtype.fields:
        new_dtype.append((f, a.dtype[f]))
    for f in b.dtype.fields:
        new_dtype.append((f, b.dtype[f]))
        
    new_dtype = numpy.dtype(new_dtype)

    c = numpy.ndarray(shape=a.shape, dtype=new_dtype)
    for f in a.dtype.fields:
        c[f] = a[f][:]
    for f in b.dtype.fields:
        c[f] = b[f][:]
    return c



def normalize(v):
    ''' Normalizes a vector by its length. '''
    return v / numpy.linalg.norm(v)


def filter_rows(rows, options):
    
    attitude_algo = 'ROLL0PITCH0'
    
    extra = numpy.ndarray(dtype=additional_fields, shape=rows.shape)
    
    minimum_linear_velocity = 0.02
    
    dt = 1/60.0
    extra['time'] = (rows['frame'] - rows['frame'][0]) / 60.0
    
    
    x = rows['x']
    y = rows['y']
    z = rows['z']
    xvel = rows['xvel']
    yvel = rows['yvel']
    zvel = rows['zvel']
    
    # save it for reference
    extra['zvel_debug'][:] = zvel[:]
    zvel = compute_derivative(z, extra['time']) 
    rows['zvel'][:] = zvel[:]
    
    xacc = compute_derivative(xvel, extra['time'])
    yacc = compute_derivative(yvel, extra['time'])
    zacc = compute_derivative(zvel, extra['time'])

    position = extra['position']
    attitude = extra['attitude']
    linear_velocity_world = extra['linear_velocity_world']
    reduced_angular_orientation = extra['reduced_angular_orientation']
    linear_velocity_modulus = extra['linear_velocity_modulus']
    linear_velocity_body = extra['linear_velocity_body']
    linear_acceleration_world = extra['linear_acceleration_world']
    linear_acceleration_body = extra['linear_acceleration_body']
    linear_acceleration_modulus = extra['linear_acceleration_modulus']
    angular_velocity_body = extra['angular_velocity_body']
    
       
    for i in xrange(len(extra)):
        position[i] = numpy.array([x[i], y[i], z[i]])
        linear_velocity_world[i] = numpy.array([xvel[i], yvel[i], zvel[i]])
        linear_acceleration_world[i] = numpy.array([xacc[i], yacc[i], zacc[i]])
        linear_velocity_modulus[i] = numpy.linalg.norm(linear_velocity_world[i]) 
        linear_acceleration_modulus[i]= numpy.linalg.norm(linear_acceleration_world[i])


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
            raise Exception('Unknown attitude algo "%s".' % attitude_algo)
        
        front = numpy.dot(attitude[i], [1, 0, 0])
        reduced_angular_orientation[i] = numpy.arctan2(front[1], front[0])

                
#        theta_simple = numpy.arctan2(linear_velocity_world[i][1],
#                     linear_velocity_world[i][0])
#        R = rotz(theta_simple)
        #print "Theta: %f deg   or  %f deg " % \
        #    (numpy.radians(reduced_angular_orientation[i]),
        #                numpy.radians(theta_simple))
            
        #print numpy.dot(R.T, attitude[i])                
                
        # compute quantities in body reference
        linear_velocity_body[i] = numpy.dot(attitude[i].T, linear_velocity_world[i])
        linear_acceleration_body[i] = numpy.dot(attitude[i].T, linear_acceleration_world[i])
        
        angular_velocity_body[i] = 0

    
    # Take care of rollover
    
    reduced_angular_orientation[:] = straighten_up_theta(reduced_angular_orientation[:])
#    
#    v = compute_derivative(reduced_angular_orientation, [0, 1])
#    for i in range(len(v)):
#        extra['reduced_angular_velocity'][i] = normalize_pi(v[i]) / dt
#    
    extra['reduced_angular_velocity'] =  compute_derivative(reduced_angular_orientation, 
                                                            extra['time'])

    # todo: make it smarter
    extra['reduced_angular_acceleration'] = \
        compute_derivative(extra['reduced_angular_velocity'], extra['time'])

    
#    # smooth both to compute angular velocity
#    annotations['linear_velocity_modulus_smooth'] = \
#        smooth1d(annotations['linear_velocity_modulus'],
#                 window_len=5, window='hanning')
#    annotations['linear_acceleration_modulus_smooth'] = \
#        smooth1d(annotations['linear_acceleration_modulus'],
#                 window_len=5, window='hanning')
#    
#    #annotations['angular_velocity_modulus'] = \
#    #   annotations['linear_acceleration_modulus'] / annotations['linear_velocity_modulus']
#    annotations['angular_velocity_modulus'] = \
#        annotations['linear_acceleration_modulus_smooth'] / \
#        annotations['linear_velocity_modulus_smooth']
    
 
    return merge_fields(rows, extra)


def straighten_up_theta(theta):
    theta2 = numpy.ndarray(shape=theta.shape, dtype=theta.dtype)
    theta2[0] = theta[0]
    for i in range(1, len(theta)):
        diff = normalize_pi(theta[i]-theta[i-1])
        theta2[i] = theta2[i-1] + diff
    return theta2
        
        
        
        
        
        
    


        

