from setuptools import setup

setup(name='flydra_render',
    version="0.1",
      package_dir={'':'src'},
      install_requires=['flydra', 'geometric_saccade_detector', 'progressbar' ],
      py_modules=['rfsee', 'flydra_osg',
                   'flydra_render', 'procgraph_flydra', 'mamarama_analysis'],
      entry_points={
         'console_scripts': [
           'flydra_render_filter      = flydra_render.main_filter:main',
           'flydra_render             = flydra_render.main_render:main',
           'flydra_render_hallucinations = flydra_render.main_render_hallucinations:main',
           'flydra_db_check           = flydra_render.db_check:main',
           'flydra_render_contrast    = flydra_render.compute_contrast:main',
           'flydra_video_contrast     = procgraph_flydra.video_contrast:main',
           'mamarama_first_order      = mamarama_analysis.first_order:main',
           'mamarama_check_stats      = mamarama_analysis.check_stats:main',
           'flydra_video_image        = procgraph_flydra.video_image:main',
           'flydra_run_pg_model       = procgraph_flydra.run_pg_model:main',
           
           # saccade analysis
           'flydra_render_saccades    = flydra_render.render_saccades:main',
           'saccades_view_analysis    = mamarama_analysis.saccades_view_analysis:main',
           'saccades_view_show        = mamarama_analysis.saccades_view_show:main',
           
           'rfsee_server = rfsee.rfsee_server:main',
           'rfsee_demo_pipe = rfsee.demo.demo_pipe:main',
           'rfsee_demo_pipe_rotation = rfsee.demo.demo_pipe_rotation:main',
           'rfsee_demo_tcp = rfsee.demo.demo_tcp:main',
           'rfsee_demo_tcp_benchmark = rfsee.demo.demo_tcp_benchmark:main',
        ]
      },
)


