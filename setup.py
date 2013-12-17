from setuptools import setup, find_packages

setup(
    name = 'Datapedia',
    version = None, # not released yet :P
    description = 'Datapedia, the Wikipedia of data!',
    license = 'GPLv3',
    author = 'Guillaume Poirier-Morency',
    author_email = 'guillaumepoiriermorency@gmail.com',
    url = 'http://github.com/arteymix/datapedia/',
    download_url = 'https://github.com/arteymix/datapedia/archive/master.zip',
    packages = find_packages(),
    requires = ['flask (>=0.10.1)'],
    test_suite = 'tests',
)
