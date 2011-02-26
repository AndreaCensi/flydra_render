from setuptools import setup
from setup_info import console_scripts #@UnresolvedImport

setup(name='flydra_render',
    version="0.1",
      package_dir={'':'src'},
      install_requires=['flydra', 'progressbar',
       # for rfsee
       'python-cjson'],
      packages=['flydra_osg','flydra_render', 'procgraph_flydra', 
                'mamarama_analysis'],
      entry_points={ 'console_scripts': console_scripts},
)


