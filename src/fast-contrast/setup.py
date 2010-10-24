from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import numpy

ext_modules = [Extension("fast_contrast", ["fast_contrast.pyx"],
                         include_dirs=[numpy.get_include()])]

setup(
  name='fast contrast computation',
  cmdclass={'build_ext': build_ext},
  ext_modules=ext_modules
)
