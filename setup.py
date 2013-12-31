from setuptools import setup, find_packages, Command

from datapedia import app

class RunCommand(Command):
    description = 'Run Datapedia HTTP server on a local port.'
    user_options = []
    
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        app.config.from_object('datapedia.config.DevelopmentConfig')
        app.run()

setup(
    name = 'Datapedia',
    version = None, # not released yet :P
    description = 'Datapedia, the Wikipedia of data!',
    license = 'GPLv3',
    author = 'Guillaume Poirier-Morency',
    author_email = 'guillaumepoiriermorency@gmail.com',
    url = 'http://github.com/arteymix/datapedia/',
    download_url = 'https://github.com/arteymix/datapedia/archive/master.zip',
    packages = ['datapedia'],
    requires = ['flask (>=0.10.1)'],
    cmdclass = {
        'run': RunCommand
    },
    test_suite = 'tests',
)
