from setuptools import setup

setup(name='flydra_render',
    version="0.1",
      package_dir={'':'src'},
      py_modules=['flydra_render'],
      install_requires=['geometric_saccade_detector'],
      entry_points={
         'console_scripts': [
           'flydra_render      = flydra_render.main:main'
        ]
      },
)


