import numpy
from procgraph_flydra.fsee_cairo import draw_fly_optics
import cairo

def create_eye_map(width, height):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    cr.translate(width / 2, height / 2)
    # note the minus here
    cr.scale(-width / 2, height / 2)
    
    cr.set_line_width(0.01)
    
    data = numpy.frombuffer(surface.get_data(), numpy.uint8)
    data.shape = (height, width, 4)

    n = 1398

    M = numpy.zeros((height, width), dtype='int')
    M[:, :] = n # out of the buffer
    
    for k in range(n):
        # draw only the k-th ommatidium
        values = numpy.zeros(shape=(n))
        values[k] = 1 
        
        # set everything to zero on the buffer
        data[:, :, 1] = 0
        # then draw it
        draw_fly_optics(cr, values, optics='buchner71')
        
        # find the pixels that were used
        z = numpy.squeeze(data[:, :, 1])
        used = z > 0
        i, j = numpy.nonzero(used)
        
        M[i, j] = k
        print  "%4d/%d %4d pixels" % (k, n, len(i))
    
    filename = 'optics_%sx%s.py' % (width, height)
    with open(filename, 'w') as f:
        f.write('# autogenerated file\n')
        data = M.tolist()
        f.write('pixelmap = %s \n' % data.__repr__())


if __name__ == '__main__':

    # create_eye_map(480, 240)
    create_eye_map(480, 240)
    #create_eye_map(640, 320)
    
