.. highlight:: shell

============
Installation
============


Stable release
--------------

To install cdptools, run this command in your terminal:

.. code-block:: console

    $ pip install cdptools

This is the preferred method to install cdptools, as it will always install the most recent stable release.

The above command only installs the basic dependencies of the project.
As each CDP instance is different, you will need to install the dependencies speicifc to that instance:

* Seattle: ``pip install cdptools[google-cloud]``

Or to install dependencies for all cities use:

.. code-block:: console

    $ pip install cdptools[all]

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for cdptools can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/CouncilDataProject/cdptools

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/CouncilDataProject/cdptools/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/CouncilDataProject/cdptools
.. _tarball: https://github.com/CouncilDataProject/cdptools/tarball/master
