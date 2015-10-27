from setuptools import setup
#from disttest import test

# Import this to prevent spurious error: info('process shutting down')
from multiprocessing import util

setup(name='apt-tools',
      version='0.1',
      description='Tools for processing APT files',
      author='Julie Weeds',
      #author_email='flyingcircus@example.com',
      license='MIT',
      packages=['src/tools']
      #cmdclass = {'test': test},
      #options = {'test' : {'test_dir':['test']}}
      #zip_safe=False
      )
