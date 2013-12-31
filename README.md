# Datapedia
Datapedia is a Wikipedia-like website designed for providing raw data instead of human-readable articles. The key point of this project is make data easily accessible for any developers.

It is designed in a non-regressive way, which means that if your application is binded to datapedia, it shall theoritically never breaks. This is done through recursive analysis of data structure to ensure that no type has changed. Data can get more complex, but are always retrocompatible.

Official documentation is available within the project.

## Installing
To install Datapedia on your computer, you need Python with the Flask framework.

    pip install flask

## Running
To run Datapedia, simply launche the run command.

    python setup.py run

## API versionning
Datapedia is versionned using git tags and the versionize decorator. This is a very special decorator which role is to enforce version usage and bind legacy action when necessary.

By default, it makes a version check with app.config['VERSION']. For example, this action is enforced to be called only from versions newer than the 1.0.

    @app.route('/<version(>1.0):version>/<action>')
    def action(version, action):
        pass

Older actions are stored in the legacy.version package. An old action could be triggered, for example: 

    @app.route('<version(>= 1.1.0):version>/<action>/<int:id>')
    def action(version, action, id):
        pass

On a production server, 
