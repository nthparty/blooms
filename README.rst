======
blooms
======

Lightweight Bloom filter data structure derived from the built-in bytearray type.

|pypi| |readthedocs| |actions| |coveralls|

.. |pypi| image:: https://badge.fury.io/py/blooms.svg#
   :target: https://badge.fury.io/py/blooms
   :alt: PyPI version and link.

.. |readthedocs| image:: https://readthedocs.org/projects/blooms/badge/?version=latest
   :target: https://blooms.readthedocs.io/en/latest/?badge=latest
   :alt: Read the Docs documentation status.

.. |actions| image:: https://github.com/nthparty/blooms/workflows/lint-test-cover-docs/badge.svg#
   :target: https://github.com/nthparty/blooms/actions/workflows/lint-test-cover-docs.yml
   :alt: GitHub Actions status.

.. |coveralls| image:: https://coveralls.io/repos/github/nthparty/blooms/badge.svg?branch=main
   :target: https://coveralls.io/github/nthparty/blooms?branch=main
   :alt: Coveralls test coverage summary.

Purpose
-------

.. |bytearray| replace:: ``bytearray``
.. _bytearray: https://docs.python.org/3/library/stdtypes.html#bytearray

This library provides a simple and lightweight data structure for representing `Bloom filters <https://en.wikipedia.org/wiki/Bloom_filter>`__ that is derived from the built-in |bytearray|_ type. The data structure has methods for the insertion, membership, union, and subset operations. In addition, methods for estimating capacity and for converting to and from Base64 strings are available.

Installation and Usage
----------------------
This library is available as a `package on PyPI <https://pypi.org/project/blooms>`__:

.. code-block:: bash

    python -m pip install blooms

The library can be imported in the usual ways:

.. code-block:: python

    import blooms
    from blooms import blooms

Examples
^^^^^^^^
This library makes it possible to concisely create, populate, and query simple `Bloom filters <https://en.wikipedia.org/wiki/Bloom_filter>`__. The example below constructs a Bloom filter that is 32 bits (*i.e.*, four bytes) in size:

.. code-block:: python

    >>> from blooms import blooms
    >>> b = blooms(4)

.. |insertion_operator| replace:: insertion operator ``@=``
.. _insertion_operator: https://blooms.readthedocs.io/en/2.0.0/_source/blooms.html#blooms.blooms.blooms.__imatmul__

A bytes-like object can be inserted into an instance using the |insertion_operator|_. It is the responsibility of the user of the library to hash and truncate the bytes-like object being inserted. Only the bytes that remain after truncation contribute to the membership of the bytes-like object within the Bloom filter:

.. code-block:: python

    >>> from hashlib import sha256
    >>> x = 'abc' # Value to insert.
    >>> h = sha256(x.encode()).digest() # Hash of value.
    >>> t = h[:2] # Truncated hash.
    >>> b @= t # Insert the value into the Bloom filter.
    >>> b.hex()
    '00000004'

.. |membership_operator| replace:: membership operator ``@``
.. _membership_operator: https://blooms.readthedocs.io/en/2.0.0/_source/blooms.html#blooms.blooms.blooms.__rmatmul__

When testing whether a bytes-like object is a member using the |membership_operator|_ of an instance, the same hashing and truncation operations should be applied:

.. code-block:: python

    >>> sha256('abc'.encode()).digest()[:2] @ b
    True
    >>> sha256('xyz'.encode()).digest()[:2] @ b
    False


The |insertion_operator|_ also accepts iterable containers:

.. code-block:: python

    >>> x = sha256('x'.encode()).digest()[:2]
    >>> y = sha256('y'.encode()).digest()[:2]
    >>> z = sha256('z'.encode()).digest()[:2]
    >>> b @= [x, y, z]
    >>> b.hex()
    '02200006'

.. |union_operator| replace:: built-in ``|`` operator
.. _union_operator: https://blooms.readthedocs.io/en/2.0.0/_source/blooms.html#blooms.blooms.blooms.__or__

The union of two Bloom filters (both having the same size) can be computed via the |union_operator|_:

.. code-block:: python

    >>> c = blooms(4)
    >>> c @= sha256('xyz'.encode()).digest()[:2]
    >>> d = c | b
    >>> sha256('abc'.encode()).digest()[:2] @ d
    True
    >>> sha256('xyz'.encode()).digest()[:2] @ d
    True

It is also possible to check whether the members of one Bloom filter `are a subset <https://blooms.readthedocs.io/en/2.0.0/_source/blooms.html#blooms.blooms.blooms.issubset>`__ of the members of another Bloom filter:

.. code-block:: python

    >>> b.issubset(c)
    False
    >>> b.issubset(d)
    True

.. |saturation| replace:: ``saturation``
.. _saturation: https://blooms.readthedocs.io/en/2.0.0/_source/blooms.html#blooms.blooms.blooms.saturation

.. |float| replace:: ``float``
.. _float: https://docs.python.org/3/library/functions.html#float

The |saturation|_ method calculates the saturation of a Bloom filter. The *saturation* is a |float|_ value (between ``0.0`` and ``1.0``) that represents an upper bound on the rate with which false positives will occur when testing bytes-like objects (of a specific length) for membership within the Bloom filter:

.. code-block:: python

    >>> b = blooms(32)
    >>> from secrets import token_bytes
    >>> for _ in range(8):
    ...     b @= token_bytes(4)
    >>> b.saturation(4)
    0.03125

.. |capacity| replace:: ``capacity``
.. _capacity: https://blooms.readthedocs.io/en/2.0.0/_source/blooms.html#blooms.blooms.blooms.capacity

It is also possible to determine the approximate maximum capacity of a Bloom filter for a given saturation limit using the |capacity|_ method. For example, the output below indicates that a saturation of ``0.05`` will likely be reached after more than ``28`` insertions of bytes-like objects of length ``8``:

.. code-block:: python

    >>> b = blooms(32)
    >>> b.capacity(8, 0.05)
    28

In addition, conversion methods to and from Base64 strings are included to support concise encoding and decoding:

.. code-block:: python

    >>> b.to_base64()
    'AiAABg=='
    >>> sha256('abc'.encode()).digest()[:2] @ blooms.from_base64('AiAABg==')
    True

.. |specialize| replace:: ``specialize``
.. _specialize: https://blooms.readthedocs.io/en/2.0.0/_source/blooms.html#blooms.blooms.blooms.specialize

If it is preferable to have a Bloom filter data structure that encapsulates a particular serialization, hashing, and truncation scheme, the recommended approach is to define a derived class. The |specialize|_ method makes it possible to do so in a concise way:

.. code-block:: python

    >>> encode = lambda x: sha256(x).digest()[:2]
    >>> blooms_custom = blooms.specialize(name='blooms_custom', encode=encode)
    >>> b = blooms_custom(4)
    >>> b @= bytes([1, 2, 3])
    >>> bytes([1, 2, 3]) @ b
    True

.. |from_base64| replace:: ``from_base64``
.. _from_base64: https://blooms.readthedocs.io/en/2.0.0/_source/blooms.html#blooms.blooms.blooms.from_base64

The user of the library is responsible for ensuring that Base64-encoded Bloom filters are converted back into an an instance of the appropriate derived class by using the |from_base64|_ method that belongs to that derived class:

.. code-block:: python

    >>> isinstance(blooms_custom.from_base64(b.to_base64()), blooms_custom)
    True

Development
-----------
All installation and development dependencies are fully specified in ``pyproject.toml``. The ``project.optional-dependencies`` object is used to `specify optional requirements <https://peps.python.org/pep-0621>`__ for various development tasks. This makes it possible to specify additional options (such as ``docs``, ``lint``, and so on) when performing installation using `pip <https://pypi.org/project/pip>`__:

.. code-block:: bash

    python -m pip install ".[docs,lint]"

Documentation
^^^^^^^^^^^^^
The documentation can be generated automatically from the source files using `Sphinx <https://www.sphinx-doc.org>`__:

.. code-block:: bash

    python -m pip install ".[docs]"
    cd docs
    sphinx-apidoc -f -E --templatedir=_templates -o _source .. && make html

Testing and Conventions
^^^^^^^^^^^^^^^^^^^^^^^
All unit tests are executed and their coverage is measured when using `pytest <https://docs.pytest.org>`__ (see the ``pyproject.toml`` file for configuration details):

.. code-block:: bash

    python -m pip install ".[test]"
    python -m pytest

The subset of the unit tests included in the module itself and can be executed using `doctest <https://docs.python.org/3/library/doctest.html>`__:

.. code-block:: bash

    python src/blooms/blooms.py -v

Style conventions are enforced using `Pylint <https://pylint.readthedocs.io>`__:

.. code-block:: bash

    python -m pip install ".[lint]"
    python -m pylint src/blooms test/test_blooms.py

Contributions
^^^^^^^^^^^^^
In order to contribute to the source code, open an issue or submit a pull request on the `GitHub page <https://github.com/nthparty/blooms>`__ for this library.

Versioning
^^^^^^^^^^
The version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`__.

Publishing
^^^^^^^^^^
This library can be published as a `package on PyPI <https://pypi.org/project/blooms>`__ via the GitHub Actions workflow found in ``.github/workflows/build-publish-sign-release.yml`` that follows the `recommendations found in the Python Packaging User Guide <https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/>`__.

Ensure that the correct version number appears in ``pyproject.toml``, and that any links in this README document to the Read the Docs documentation of this package (or its dependencies) have appropriate version numbers. Also ensure that the Read the Docs project for this library has an `automation rule <https://docs.readthedocs.io/en/stable/automation-rules.html>`__ that activates and sets as the default all tagged versions.

To publish the package, create and push a tag for the version being published (replacing ``?.?.?`` with the version number):

.. code-block:: bash

    git tag ?.?.?
    git push origin ?.?.?
