from setuptools import setup
from os import path


def ga(t, ec, ea, el, cid, ev=False, v=1, tid='UA-115550236-2', extras={}):

    params = {
        't': t,
        'ec': ec,
        'ea': ea, 
        'el': el,
        'v': v,
        'tid': tid,
        'cid': cid
        }

    params.update(extras)

    if ev:
        params['ev'] = ev

    uri = "https://www.google-analytics.com/collect"

    try:
        r = requests.post(uri, data = urllib.urlencode(params), headers={'referer': 'http://cli.threshingfloor.io'})
    except Exception as e:
        print(e)


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='tf-reaper',
    version = '0.0.6',
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

ga('event', 'CLI', 'install', 'CLI Installed', "000")

message = """
__________                                   
\______   \ ____ _____  ______   ___________ 
 |       _// __ \\__  \ \____ \_/ __ \_  __ \
 |    |   \  ___/ / __ \|  |_> >  ___/|  | \/
 |____|_  /\___  >____  /   __/ \___  >__|   
        \/     \/     \/|__|        \/       

If you do not have an API key, request one at info@threshingfloor.io

To get started, run \'\$ reaper -h\'
"""
