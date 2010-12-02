import numpy
from numpy import array
from StringIO import StringIO

from procgraph  import Block
from procgraph_mpl import pylab2rgb 

from flydra_db import FlydraDB

def get_posts_info(xml):
    from flydra.a2 import xml_stimulus #@UnresolvedImport
    stimulus_xml = StringIO(xml)
    stim_xml = xml_stimulus.xml_stimulus_from_filename(stimulus_xml)
    root = stim_xml.get_root()
    
    results = {'posts':[]}
    for child in root:
        if child.tag == 'cylindrical_post':
            info = stim_xml._get_info_for_cylindrical_post(child)
            results['posts'].append(info)
        elif child.tag == 'cylindrical_arena':
            results['arena'] = stim_xml._get_info_for_cylindrical_arena(child)

    return results
          
#
#ss
#mamarama_radius = 1.0
#mamarama_center = [0.15, 0.48]
#mamarama_height = 0.8

class LookupInfo:
    
    def init(self):
        if self.config.db is not None and self.config.sample is not None:
            db = FlydraDB(self.config.db)
            stimulus_xml = db.get_attr(self.config.sample, 'stimulus_xml')
            self.arena_info = get_posts_info(stimulus_xml)
        else:
            self.arena_info = None
 
class ArenaDisplayTop(LookupInfo, Block):
    ''' Produces a top-down plot of a circular arena.
    '''
    
    Block.alias('arena_display_top')
    
    Block.config('width', 'Image width in pixels.', default=320)
     
    Block.config('sample', default=None)
    Block.config('db', default=None)
    
    Block.input('position', 'Assumed to be a numpy ')
    
    Block.output('rgb', 'RGB image.')
      
            
    def update(self):        
        position = array(self.input.position)
        import matplotlib
        matplotlib.use('agg', warn=False)
        from matplotlib import pylab
        
        f = pylab.figure(frameon=False,
                        figsize=(self.config.width / 100.0,
                                 self.config.width / 100.0))
    
        if self.arena_info:
            plot_posts_xy(pylab, self.arena_info)
    
    
        x = position[:, 0]
        y = position[ :, 1]
         
        pylab.plot(x, y, 'b-')
            
        R = self.arena_info['arena']['diameter'] / 2 
        cx = self.arena_info['arena']['origin'][0]
        cy = self.arena_info['arena']['origin'][1]
         
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

   
def plot_posts_xy(pylab, info):
    for post in info['posts']:
        p1 = post['verts'][0]
        p2 = post['verts'][1]        
        pylab.plot([p1[0], p2[0]], [p1[1], p2[1]], 'k-', linewidth=3)

def plot_posts_xz(pylab, info):
    for post in info['posts']:
        p1 = post['verts'][0]
        p2 = post['verts'][1]        
        pylab.plot([p1[0], p2[0]], [p1[2], p2[2]], 'k-', linewidth=3)
        
   
class ArenaDisplaySide(LookupInfo, Block):
    ''' Produces a side plot (x,z) of a circular arena.
    '''
    
    Block.alias('arena_display_side')
    Block.config('sample', default=None)
    Block.config('db', default=None)
    
    
    Block.config('width', 'Image width in pixels.', default=320)
 
    Block.input('position', 'Assumed to be a numpy ')
    

    Block.output('rgb', 'RGB image.')
      
        
    def update(self):
        position = array(self.input.position)
        
        R = self.arena_info['arena']['diameter'] / 2 
        cx = self.arena_info['arena']['origin'][0]
        # cy = self.arena_info['arena']['origin'][1]
        h = self.arena_info['arena']['height']
        
        width = self.config.width
        height = h / (2 * R) * width
        
        
        import matplotlib
        matplotlib.use('agg', warn=False)
        from matplotlib import pylab
        
        f = pylab.figure(frameon=False,
                        figsize=(width / 100.0,
                                 height / 100.0)) 
    
        
        plot_posts_xz(pylab, self.arena_info)
        
            
        x = position[:, 0]
        z = position[:, 2]
         
        pylab.plot(x, z, 'b-')
        
         
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



class ArenaDisplayTopZoom(LookupInfo, Block):
    ''' Produces a top-down plot of a circular arena.
    '''
    
    Block.alias('arena_display_top_zoom')
    
    Block.config('sample', default=None)
    Block.config('db', default=None)
    
    
    Block.config('width', 'Image width in pixels.', default=320)
    
    Block.config('zoom_area', default=0.1)
    Block.config('arrow_length', default=0.02)
    
    Block.input('position')
    Block.input('attitude') 
    
    Block.output('rgb', 'RGB image.')
      
        
    def update(self):        
        position = array(self.input.position)
        
        import matplotlib
        matplotlib.use('agg', warn=False)
        from matplotlib import pylab
        
        f = pylab.figure(frameon=False,
                        figsize=(self.config.width / 100.0,
                                 self.config.width / 100.0))
         
 
        plot_posts_xy(pylab, self.arena_info)
    
        x = position[:, 0]
        y = position[ :, 1]
        xc = x[-1]
        yc = y[-1]
        
         
        pylab.plot(x, y, 'b.')
        
        attitude = self.input.attitude
        
        fwd = numpy.dot(attitude, [1, 0, 0]) * self.config.arrow_length
        pylab.plot([xc, xc + fwd[0] ], [yc, yc + fwd[1]])
        
            
        Z = self.config.zoom_area
        
        R = self.arena_info['arena']['diameter'] / 2 
        cx = self.arena_info['arena']['origin'][0]
        cy = self.arena_info['arena']['origin'][1]
         
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



class ArenaDisplaySideZoom(LookupInfo, Block):
    ''' Produces a side plot (x,z) of a circular arena.
    '''
    
    Block.alias('arena_display_side_zoom')
    
    Block.config('sample', default=None)
    Block.config('db', default=None)
    
    
    Block.config('width', 'Image width in pixels.', default=320)
    Block.config('zoom_area', default=0.1)
      
    Block.input('position', 'Assumed to be a numpy ') 
    
    
    Block.output('rgb', 'RGB image.')
      
        
    def update(self):        
        R = self.arena_info['arena']['diameter'] / 2 
        cx = self.arena_info['arena']['origin'][0]
        # cy = self.arena_info['arena']['origin'][1]
        h = self.arena_info['arena']['height']

        
        width = self.config.width
        ratio = h / (2 * R)
        height = ratio * width
        
        
        import matplotlib
        matplotlib.use('agg', warn=False)
        from matplotlib import pylab
        
        f = pylab.figure(frameon=False,
                        figsize=(width / 100.0,
                                 height / 100.0))
              
        plot_posts_xz(pylab, self.arena_info)
    
        position = array(self.input.position)
        
        x = position[:, 0]
        z = position[:, 2]
        xl = x[-1]
        zl = z[-1]
         
        pylab.plot(x, z, 'b.')
            
         
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
