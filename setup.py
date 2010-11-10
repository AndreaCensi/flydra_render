from setuptools import setup
from setup_info import console_scripts

setup(name='flydra_render',
    version="0.1",
      package_dir={'':'src'},
      install_requires=['flydra', 'geometric_saccade_detector', 'progressbar' ],
      packages=['rfsee', 'flydra_osg',
                   'flydra_render', 'procgraph_flydra', 'mamarama_analysis'],
      entry_points={ 'console_scripts': console_scripts},
)


