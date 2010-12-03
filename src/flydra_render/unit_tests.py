import numpy, unittest 

from .main_filter_meat import compute_derivative


class UtilsTest(unittest.TestCase): 

    def derivative_test(self):
        
        t = numpy.linspace(1, 10, 20)
        x = t ** 2
        
        dx = compute_derivative(x, t)
        ddx = compute_derivative(dx, t)
        
        self.assertTrue((dx >= 0).all())
        self.assertTrue((ddx >= 0).all())
