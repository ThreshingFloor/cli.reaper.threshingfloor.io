from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='tf-reaper',
    version = '0.0.8',
    license = 'MIT',
    author = 'Threshing Floor Security, LLC',
    author_email = 'info@threshingfloor.io',
    description = 'Threshing Floor CLI utility for analyzing log files for noise.',
    long_description = long_description,
    scripts = ['reaper'],
    install_requires = ['libtf', 'requests'],
    url = 'https://github.com/ThreshingFloor/cli.reaper.threshingfloor.io',
    classifiers = ['Development Status :: 3 - Alpha'],
    )

message = """

__________                                   
\______   \ ____ _____  ______   ___________    
 |       _// __ \\\\__  \ \\____ \\_/ __ \\_  __ \\ 
 |    |   \  ___/ / __ \|  |_> >  ___/|  | \/ 
 |____|_  /\___  >____  /   __/ \___  >__|    
        \/     \/     \/|__|        \/        

If you do not have an API key, request one at info@threshingfloor.io

To get started, run \'$ reaper -h\'
"""

print(message)
