from numpy import array
from matplotlib import pylab

from procgraph  import Block
from procgraph.components.gui.plot import pylab2rgb
from procgraph.core.exceptions import BadInput
import numpy


mamarama_radius = 1.0
mamarama_center = [0.15, 0.48]
mamarama_height = 0.8

class ArenaDisplayTop(Block):
    ''' Produces a top-down plot of a circular arena.
    '''
    
    Block.alias('arena_display_top')
    
    Block.config('width', 'Image width in pixels.', default=320)
    Block.config('arena_radius', 'Radius of the arena (m).', default=mamarama_radius)
    Block.config('arena_center', 'Coordinates of the center.', default=mamarama_center)
    
    Block.input('position', 'Assumed to be a numpy ')
    
    Block.output('rgb', 'RGB image.')
      
        
    def update(self):        
        position = array(self.input.position)
        f = pylab.figure(frameon=False,
                        figsize=(self.config.width / 100.0,
                                 self.config.width / 100.0))
            
        x = position[:, 0]
        y = position[ :, 1]
         
        pylab.plot(x, y, 'b-')
            
        R = self.config.arena_radius
        cx = self.config.arena_center[0]
        cy = self.config.arena_center[1]
         
        # draw arena
        theta = numpy.linspace(0, numpy.pi * 2.01, 500)
        x = numpy.cos(theta) * R + cx
        y = numpy.sin(theta) * R + cy
        pylab.plot(x, y, 'k-')
         
        R *= 1.1
        pylab.axis([-R + cx , R + cx, -R + cy, R + cy])

        # turn off ticks labels
        pylab.setp(f.axes[0].get_xticklabels(), visible=False)
        pylab.setp(f.axes[0].get_yticklabels(), visible=False)
   
        self.output.rgb = pylab2rgb(transparent=False, tight=True)

        pylab.close(f.number)


class ArenaDisplaySide(Block):
    ''' Produces a side plot (x,z) of a circular arena.
    '''
    
    Block.alias('arena_display_side')
    
    Block.config('width', 'Image width in pixels.', default=320)
    Block.config('arena_radius', 'Radius of the arena (m).', default=mamarama_radius)
    Block.config('arena_center', 'Coordinates of the center.', default=mamarama_center)
    Block.config('arena_height', 'Coordinates of the center.', default=mamarama_height)
    
    Block.input('position', 'Assumed to be a numpy ')
    
    Block.output('rgb', 'RGB image.')
      
        
    def update(self):        
        position = array(self.input.position)
        
        width = self.config.width
        height = self.config.arena_height / (2 * self.config.arena_radius) * width
        
        f = pylab.figure(frameon=False,
                        figsize=(width / 100.0,
                                 height / 100.0))
            
        x = position[:, 0]
        z = position[:, 2]
         
        pylab.plot(x, z, 'b-')
            
        R = self.config.arena_radius
        cx = self.config.arena_center[0]
        cy = self.config.arena_center[1]
        h = self.config.arena_height
         
        # draw arena
        x = [cx - R, cx - R, cx + R, cx + R, cx - R]
        z = [0, h, h, 0, 0]
        pylab.plot(x, z, 'k-')
         
        R *= 1.1
        pylab.axis([-R + cx , R + cx, -0.05, h + 0.05])

        # turn off ticks labels
        pylab.setp(f.axes[0].get_xticklabels(), visible=False)
        pylab.setp(f.axes[0].get_yticklabels(), visible=False)
   
        self.output.rgb = pylab2rgb(transparent=False, tight=True)

        pylab.close(f.number)



class ArenaDisplayTopZoom(Block):
    ''' Produces a top-down plot of a circular arena.
    '''
    
    Block.alias('arena_display_top_zoom')
    
    Block.config('width', 'Image width in pixels.', default=320)
    Block.config('arena_radius', 'Radius of the arena (m).', default=mamarama_radius)
    Block.config('arena_center', 'Coordinates of the center.', default=mamarama_center)
    Block.config('arena_height', 'Coordinates of the center.', default=mamarama_height)

    Block.config('zoom_area', default=0.1)
    Block.config('arrow_length', default=0.02)
    
    Block.input('position')
    Block.input('attitude')
    
    Block.output('rgb', 'RGB image.')
      
        
    def update(self):        
        position = array(self.input.position)
        f = pylab.figure(frameon=False,
                        figsize=(self.config.width / 100.0,
                                 self.config.width / 100.0))
            
        x = position[:, 0]
        y = position[ :, 1]
        xc = x[-1]
        yc = y[-1]
        
         
        pylab.plot(x, y, 'b.')
        
        attitude = self.input.attitude
        
        fwd = numpy.dot(attitude, [1, 0, 0]) * self.config.arrow_length
        pylab.plot([xc, xc + fwd[0] ], [yc, yc + fwd[1]])
        
            
        Z = self.config.zoom_area
        R = self.config.arena_radius
        cx = self.config.arena_center[0]
        cy = self.config.arena_center[1]
         
        # draw arena
        theta = numpy.linspace(0, numpy.pi * 2.01, 500)
        x = numpy.cos(theta) * R + cx
        y = numpy.sin(theta) * R + cy
        pylab.plot(x, y, 'k-')
         
        pylab.axis([-Z + xc , Z + xc, -Z + yc, Z + yc])

        # turn off ticks labels
        pylab.setp(f.axes[0].get_xticklabels(), visible=False)
        pylab.setp(f.axes[0].get_yticklabels(), visible=False)
   
        self.output.rgb = pylab2rgb(transparent=False, tight=True)

        pylab.close(f.number)



class ArenaDisplaySideZoom(Block):
    ''' Produces a side plot (x,z) of a circular arena.
    '''
    
    Block.alias('arena_display_side_zoom')
    
    Block.config('width', 'Image width in pixels.', default=320)
    Block.config('zoom_area', default=0.1)
    Block.config('arena_radius', 'Radius of the arena (m).', default=mamarama_radius)
    Block.config('arena_center', 'Coordinates of the center.', default=mamarama_center)
    Block.config('arena_height', 'Coordinates of the center.', default=mamarama_height)
    
    Block.input('position', 'Assumed to be a numpy ')
    
    Block.output('rgb', 'RGB image.')
      
        
    def update(self):        
        position = array(self.input.position)
        
        width = self.config.width
        ratio = self.config.arena_height / (2 * self.config.arena_radius)
        height = ratio * width
        
        f = pylab.figure(frameon=False,
                        figsize=(width / 100.0,
                                 height / 100.0))
            
        x = position[:, 0]
        z = position[:, 2]
        xl = x[-1]
        zl = z[-1]
         
        pylab.plot(x, z, 'b.')
            
        R = self.config.arena_radius
        cx = self.config.arena_center[0]
        cy = self.config.arena_center[1]
        h = self.config.arena_height
         
        # draw arena
        x = [cx - R, cx - R, cx + R, cx + R, cx - R]
        z = [0, h, h, 0, 0]
        pylab.plot(x, z, 'k-')
         
        aw = self.config.zoom_area
        ah = ratio * aw
    
        pylab.axis([ xl - aw , xl + aw, zl - ah, zl + ah])

        # turn off ticks labels
        pylab.setp(f.axes[0].get_xticklabels(), visible=False)
        pylab.setp(f.axes[0].get_yticklabels(), visible=False)
   
        self.output.rgb = pylab2rgb(transparent=False, tight=True)

        pylab.close(f.number)
