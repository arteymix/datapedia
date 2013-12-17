from setuptools import setup

setup(
    name = 'Datapedia',
    version = None, # not released yet :P
    description = 'Datapedia, the Wikipedia of data!',
    license = 'GPLv3',
    author = 'Guillaume Poirier-Morency',
    author_email = 'guillaumepoiriermorency@gmail.com',
    url = 'http://github.com/arteymix/datapedia/',
    download_url = 'https://github.com/arteymix/datapedia/archive/master.zip',
    install_requires = ['flask'],
    test_suite = 'tests'
)
