#! /usr/bin/env python
import cairo
from math import pi, sin, atan2, acos

import random
import numpy

import fsee.eye_geometry.switcher
from flydra_render.render_saccades import rotz

def sphere2surface(s, num_eye):
    phi = atan2(s[1], s[0]);
    theta = acos(s[2]);

    # x = phi / (1.1 * pi);
    x = phi / (1.18 * pi);
    
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
        
        
def draw_path(cr, points):
    cr.new_path()
    cr.move_to(points[0][0], points[0][1])
    for i in range(len(points)):
        cr.line_to(points[i][0], points[i][1])
    cr.stroke()
    
def draw_reference_lines(cr):
    gray = [0.5, 0.5, 0.5]
    #colors = {0: {0: [1, 1, 0], pi / 2:[1, 0, 1], pi  : [0, 0, 0]},
    #          1: {0: [1, 1, 0], -pi / 2:[0, 1, 1], -pi  : [0, 0, 0]}}
    colors = {0: {0:gray, pi / 2:gray, pi  : [0, 0, 0]},
              1: {0:gray, -pi / 2:gray, -pi  : [0, 0, 0]}}
              
    for eye in [0, 1]:        
        # find width of 1 pixel
        width = cr.device_to_user_distance(1, 0)[0]
        
        thetas = sorted(colors[eye].keys())
        thetas = numpy.linspace(thetas[-1], thetas[0], 100)
        S = map(lambda theta: numpy.dot(rotz(theta), [1, 0, 0]), thetas)
        points = map(lambda x: sphere2surface(x, eye * 800), S)
        cr.set_source_rgba(gray[0], gray[1], gray[2], 10)
        cr.set_line_width(width * 3.0)
        cr.set_antialias(cairo.ANTIALIAS_NONE)
        draw_path(cr, points)
        
    for eye in [0, 1]:
        cr.set_line_width(width * 1.0)    
        cr.set_antialias(cairo.ANTIALIAS_NONE)
        
        for theta, color in colors[eye].items():
            cr.set_source_rgba(color[0], color[1], color[2], 1)
            phis = numpy.linspace(-pi / 2, +pi / 2, 100)
            S = map(lambda phi: [numpy.cos(phi), 0, numpy.sin(phi)], phis)
            # rotate around z azis
            S = map(lambda s: numpy.dot(rotz(theta), s), S)
            points = map(lambda x: sphere2surface(x, eye * 800), S)
            draw_path(cr, points)
                

def quick_draw_to_file(values, width, height, filename):
#    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
#    cr = cairo.Context(surface)
#    cr.translate(-width / 2, height / 2)
#    cr.scale(-width / 2, height / 2)
    from procgraph_flydra.generate_pixel_map import setup_surface

    surface, cr = setup_surface(width, height)
    
    draw_fly_optics(cr, values, optics='buchner71')
    cr.scale(-1, 1) # strange bug
    draw_reference_lines(cr)
     
    cr.show_page()
    surface.write_to_png(filename)
    surface.finish()
 
 
if __name__ == '__main__': 
    if True:
        values = map(lambda p: random.random(), xrange(1398))
        filename = "fsee_cairo_test.png"
        print "Writing to %s" % filename
        width, height = 640, 240

        quick_draw_to_file(values=values, width=width, height=height,
                           filename=filename)
    else:
        for i in xrange(2000):
            values = map(lambda p: random.random(), xrange(1398))
            filename = 'snp_movie%03d.png' % i
            quick_draw_to_file(values=values, width=600, height=300, filename=filename)
            print i
