import numpy
from reprep import Report

from flydra_render.compute_contrast import intrinsic_contrast
from mamarama_analysis.covariance import Expectation
from procgraph_flydra.values2retina import plot_contrast, plot_luminance,\
    values2retina
from flydra_render.contrast import get_contrast_kernel, intrinsic_contrast
from flydra_render.progress import progress_bar
from flydra_render.render_saccades import rotz
from rfsee.demo.example_stimxml import example_stim_xml
from rfsee.rfsee_client import ClientProcess
from procgraph_flydra.arena_display import mamarama_center
from reprep.graphics.scale import scale


def main():
    sigma_deg =6
    kernel1 = get_contrast_kernel(sigma_deg=sigma_deg, eyes_interact=True)
    kernel2 = get_contrast_kernel(sigma_deg=sigma_deg, eyes_interact=False) # better
       
    meany = Expectation()
    ex1 = Expectation()
    ex2 = Expectation()
    
    cp = ClientProcess()
    #cp.config_use_white_arena()    
    cp.config_stimulus_xml(example_stim_xml)
    #position = [0.15, 0.5, 0.25]
    position = [0.35, 0.5, 0.25]
    linear_velocity_body = [0, 0, 0]
    angular_velocity_body = [0, 0, 0]
    
    

    N = 360
    
    pb = progress_bar('Computing contrast', N)
    
    orientation = numpy.linspace(0, 2* numpy.pi, N)
    for i, theta in enumerate(orientation):
        attitude = rotz(theta)
        
        pb.update(i)
        res = cp.render(position, attitude, 
                        linear_velocity_body, angular_velocity_body)
    
        y = numpy.array(res['luminance'])
        
        meany.update(y)
        #y = numpy.random.rand(1398)
        
        c1 = intrinsic_contrast(y, kernel1)
        c2 = intrinsic_contrast(y, kernel2)
        
    
        ex1.update(c1)
        ex2.update(c2)


    r =  Report()
    r.data_rgb('meany', scale(values2retina(meany.get_value())))
    r.data_rgb('mean1', plot_contrast(ex1.get_value()))
    r.data_rgb('mean2', plot_contrast(ex2.get_value()))
    r.data_rgb('one-y',  (plot_luminance(y)))
    r.data_rgb('one-c1',  plot_contrast(c1))
    r.data_rgb('one-c2',  plot_contrast(c2))
    
    r.data_rgb('kernel',  scale(values2retina(kernel2[100,:])))
    
    f = r.figure(shape=(2,3))
    f.sub('one-y', 'One random image')
    f.sub('one-c1', 'Contrast of random image')
    f.sub('one-c2', 'Contrast of random image')
    f.sub('meany', 'Mean luminance')
    f.sub('mean1', 'Mean over %s samples' % N)
    f.sub('mean2', 'Mean over %s samples' % N)
    f.sub('kernel')
    
    filename = 'compute_contrast_demo.html'
    print "Writing on %s" % filename
    r.to_html(filename)





if __name__ == '__main__':
    main()
    
    