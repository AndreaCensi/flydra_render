#! /usr/bin/env python
import cairo
from math import pi, sin, atan2, acos

import random
import numpy

import fsee
import fsee.eye_geometry
import fsee.eye_geometry.switcher

def sphere2surface(s, num_eye):
    phi = atan2(s[1], s[0]);
    theta = acos(s[2]);

    x = phi / (1.1 * pi);
    if num_eye < 1398 / 2:
        x = x + 0.12    
    else:
        x = x - 0.12
    y = sin((theta - pi / 2) / 1.1)

    return numpy.array([[x], [y]])

def draw_fly_optics(cr, values, optics='buchner71'):    
    precomputed = fsee.eye_geometry.switcher.get_module_for_optics(optics=optics)

    for i in xrange(len(precomputed.hex_faces)):
        # transform vertices to screen coordinates
        vertices = map(lambda p: sphere2surface(p, i), precomputed.hex_faces[i])
    
        gray = values[i]
        cr.set_source_rgba(gray, gray, gray, 1)

        cr.new_path()
        cr.move_to(vertices[-1][0], vertices[-1][1]);
        for i in xrange(len(vertices)):
            cr.line_to(vertices[i][0], vertices[i][1]);
        
        cr.fill()
        
def quick_draw_to_file(values, width, height, filename):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    cr.translate(width / 2, height / 2)
    cr.scale(width / 2, height / 2)
    
    cr.set_line_width(0.01)
    
    draw_fly_optics(cr, values, optics='buchner71')

    data = numpy.array(surface.get_data())
    print data.dtype, data.shape
     
    surface.write_to_png(filename)
    cr.show_page()
    surface.finish()
 
if __name__ == '__main__': 
    if 0:
        values = map(lambda p: random.random(), xrange(1398))
        quick_draw_to_file(values=values, width=600, height=300, filename="snp_visualize.py.png")

    if 1:
        for i in xrange(2000):
            values = map(lambda p: random.random(), xrange(1398))
            filename = 'snp_movie%03d.png' % i
            quick_draw_to_file(values=values, width=600, height=300, filename=filename)
            print i
