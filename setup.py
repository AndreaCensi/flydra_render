from setuptools import setup

setup(name='flydra_render',
    version="0.1",
      package_dir={'':'src'},
      py_modules=['flydra_render', 'procgraph_flydra'],
      install_requires=['flydra', 'geometric_saccade_detector'],
      entry_points={
         'console_scripts': [
           'flydra_render_filter      = flydra_render.main_filter:main',
           'flydra_render             = flydra_render.main_render:main',
           'flydra_render_db_check      = flydra_render.db_test:main'
        ]
      },
)


