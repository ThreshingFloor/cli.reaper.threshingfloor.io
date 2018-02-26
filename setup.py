from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='tf-reaper',
    version = '0.0.4',
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
