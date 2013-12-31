# Datapedia
Datapedia is a Wikipedia-like website designed for providing raw data instead of human-readable articles. The key point of this project is make data easily accessible for any developers.

It is designed in a non-regressive way, which means that if your application is binded to datapedia, it shall theoritically never breaks. This is done through recursive analysis of data structure to ensure that no type has changed. Data can get more complex, but are always retrocompatible.

Official documentation is available within the project.

## Installing
To install datapedia on your computer, you need Python with the Flask framework.

    pip install flask

## Running
To run Datapedia, use the run command

    python setup.py run

You can also run tests

    python setup.py test

## Configuring (optional)
To configure Datapedia, you can edit the config.py file and add your custom configuration options.

Datapedia has 3 configurations: Production, Testing and Development.

* Production is loaded on the production server.
* Testing is loaded in the setUp function in the tests
* Development is loaded by the RunCommand in setup.py
    
## Helping out!
Datapedia is a community project and thus will freely accept any kind of collaboration! There are a few things that you can do to help out.

### Write an example
If you are genuine in a language, you might want to write an example for the main Datapedia page! Ensure that you respect coding conventions and use the standard library. To know which examples are missing, visit the home page of Datapedia at http://arteymix.pythonanywhere.com/.
By default, it makes a version check with app.config['VERSION']. For example, this action is enforced to be called only from versions newer than the 1.0.

### Write documentation
Datapedia api specifications are nearly complete. However, we need some documentation for developers and users. We need to write guidelines for data structure, some howtos designed for everyday people and some text here and there. The website is self-documented: you only need to work in the templates.

### Test Datapedia
Flask has very nice testing utilities and you might want to write and run some tests.
