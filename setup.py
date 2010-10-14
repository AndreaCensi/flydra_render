from setuptools import setup

setup(name='flydra_render',
    version="0.1",
      package_dir={'':'src'},
      install_requires=['flydra', 'geometric_saccade_detector', 'progressbar', 'rfsee'],
      py_modules=['flydra_render', 'procgraph_flydra', 'mamarama_analysis'],
      entry_points={
         'console_scripts': [
           'flydra_render_filter      = flydra_render.main_filter:main',
           'flydra_render             = flydra_render.main_render:main',
           'flydra_render_db_check      = flydra_render.db_test:main',
           'flydra_render_contrast      = flydra_render.compute_contrast:main',
           'flydra_video_contrast      = procgraph_flydra.video_contrast:main',
           'mamarama_first_order      = mamarama_analysis.first_order:main'
        ]
      },
)


