===========
cdptools
===========


.. image:: https://img.shields.io/pypi/v/cdptools.svg
        :target: https://pypi.python.org/pypi/cdptools

.. image:: https://img.shields.io/travis/JacksonMaxfield/cdptools.svg
        :target: https://travis-ci.org/JacksonMaxfield/cdptools

.. image:: https://readthedocs.org/projects/cdptools/badge/?version=latest
        :target: https://cdptools.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Tools used to run Council Data Project pipelines.


* Free software: MIT license

* Documentation: https://cdptools.readthedocs.io.


Features
--------

* TODO


Notes on Hitting Exposed Database Endpoints
-------------------------------------------
`pip install git+https://github.com/ozgur/python-firebase.git`

```
from firebase import firebase
firebase = firebase.FirebaseApplication("https://your-cdp-target.firebaseio.com/")
events = firebase.get("/events", None)
```


Credits
-------

This package was created with Cookiecutter_.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
