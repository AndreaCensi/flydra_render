
scripts = [
    ('flydra_render_filter', 'flydra_render.main_filter'),
    ('flydra_render', 'flydra_render.main_render'),
    ('flydra_render_hallucinations', 'flydra_render.main_render_hallucinations'),
    ('flydra_db_check', 'flydra_db.db_check'),
    ('flydra_db_stats', 'flydra_db.db_stats'),
    ('flydra_render_contrast', 'flydra_render.compute_contrast'),
    
    ('mamarama_first_order', 'mamarama_analysis.first_order'),
    ('mamarama_check_stats', 'mamarama_analysis.check_stats'),
    ('mamarama_env_stats', 'mamarama_analysis.environment_stats'),
    
    # videos / procgraph
    ('flydra_video_contrast', 'procgraph_flydra.video_contrast'),
    ('flydra_video_image', 'procgraph_flydra.video_image'),
    ('flydra_run_pg_model', 'procgraph_flydra.run_pg_model'),
     
     # saccade analysis
    ('flydra_render_saccades', 'flydra_render.render_saccades'),
    ('flydra_render_saccades_hallucinations',
      'flydra_render.render_saccades_hallucinations'),
    ('saccades_view_analysis', 'mamarama_analysis.saccades_view_analysis'),
    ('saccades_view_joint_analysis', 'mamarama_analysis.saccades_view_joint_analysis'),
    ('saccades_view_show', 'mamarama_analysis.saccades_view_show'),
     
    # rfsee
    ('rfsee_server', 'rfsee.rfsee_server'),
    ('rfsee_demo_pipe', 'rfsee.demo.demo_pipe'),
    ('rfsee_demo_pipe_rotation', 'rfsee.demo.demo_pipe_rotation'),
    ('rfsee_demo_tcp', 'rfsee.demo.demo_tcp'),
    ('rfsee_demo_tcp_benchmark', 'rfsee.demo.demo_tcp_benchmark'),
]


# this is the format for setuptools
console_scripts = map(lambda s: '%s = %s:main' % (s[0], s[1]), scripts)
