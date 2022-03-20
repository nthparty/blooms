======
blooms
======

Lightweight Bloom filter data structure derived from the built-in bytearray type.

|pypi| |readthedocs| |actions| |coveralls|

.. |pypi| image:: https://badge.fury.io/py/blooms.svg
   :target: https://badge.fury.io/py/blooms
   :alt: PyPI version and link.

.. |readthedocs| image:: https://readthedocs.org/projects/blooms/badge/?version=latest
   :target: https://blooms.readthedocs.io/en/latest/?badge=latest
   :alt: Read the Docs documentation status.

.. |actions| image:: https://github.com/nthparty/blooms/workflows/lint-test-cover-docs/badge.svg
   :target: https://github.com/nthparty/blooms/actions/workflows/lint-test-cover-docs.yml
   :alt: GitHub Actions status.

.. |coveralls| image:: https://coveralls.io/repos/github/nthparty/blooms/badge.svg?branch=main
   :target: https://coveralls.io/github/nthparty/blooms?branch=main
   :alt: Coveralls test coverage summary.

Purpose
-------
This library provides a simple and lightweight data structure for representing `Bloom filters <https://en.wikipedia.org/wiki/Bloom_filter>`_ that is derived from the built-in `bytearray <https://docs.python.org/3/library/stdtypes.html#bytearray>`_ type. The data structure has methods for the insertion, membership, union, and subset operations. In addition, methods for converting to and from Base64 strings are included.

Package Installation and Usage
------------------------------
The package is available on `PyPI <https://pypi.org/project/blooms/>`_::

    python -m pip install blooms

The library can be imported in the usual ways::

    import blooms
    from blooms import blooms

Examples
^^^^^^^^
This library makes it possible to concisely create, populate, and query simple Bloom filters. The example below constructs a Bloom filter that is 32 bits (*i.e.*, four bytes) in size::

    >>> from blooms import blooms
    >>> b = blooms(4)

It is the responsibility of the user of the library to hash and truncate the bytes-like object being inserted so that only those bytes that contribute to the object's membership are considered::

    >>> from hashlib import sha256
    >>> x = 'abc' # Value to insert.
    >>> h = sha256(x.encode()).digest() # Hash of value.
    >>> t = h[:2] # Truncated hash.
    >>> b @= t # Insert the value into the Bloom filter.
    >>> b.hex()
    '00000004'

When testing whether a bytes-like object is a member of an instance, the same hashing and truncation operations should be applied::

    >>> sha256('abc'.encode()).digest()[:2] @ b
    True
    >>> sha256('xyz'.encode()).digest()[:2] @ b
    False

The ``@=`` operator also accepts iterable containers::

    >>> x = sha256('x'.encode()).digest()[:2]
    >>> y = sha256('y'.encode()).digest()[:2]
    >>> z = sha256('z'.encode()).digest()[:2]
    >>> b @= [x, y, z]
    >>> b.hex()
    '02200006'

The union of two Bloom filters (both having the same size) can be computed using the built-in ``|`` operator::

    >>> c = blooms(4)
    >>> c @= sha256('xyz'.encode()).digest()[:2]
    >>> d = c | b
    >>> sha256('abc'.encode()).digest()[:2] @ d
    True
    >>> sha256('xyz'.encode()).digest()[:2] @ d
    True

It is also possible to check whether the members of one Bloom filter are a subset of the members of another Bloom filter::

    >>> b.issubset(c)
    False
    >>> b.issubset(d)
    True

A method is provided for determining the saturation of a Bloom filter. The saturation is a ``float`` value (between ``0.0`` and ``1.0``) that represents an upper bound on the rate with which false positives will occur when testing bytes-like objects (of a specific length) for membership within the Bloom filter::

	>>> b = blooms(32)
	>>> from secrets import token_bytes
	>>> for _ in range(8):
	...     b @= token_bytes(4)
	>>> b.saturation(4)
	0.03125

It is also possible to determine the approximate maximum capacity of a Bloom filter for a given saturation limit. For example, the output below indicates that a saturation of ``0.05`` will likely be reached after more than ``28`` insertions of bytes-like objects of length ``8``::

	>>> b = blooms(32)
	>>> b.capacity(8, 0.05)
	28

In addition, conversion methods to and from Base64 strings are included to support concise encoding and decoding::

    >>> b.to_base64()
    'AiAABg=='
    >>> sha256('abc'.encode()).digest()[:2] @ blooms.from_base64('AiAABg==')
    True

If it is preferable to have a Bloom filter data structure that encapsulates a particular serialization, hashing, and truncation scheme, the recommended approach is to defined a derived class. The ``specialize`` method makes it possible to do so in a concise way::

    >>> encode = lambda x: sha256(x).digest()[:2]
    >>> blooms_custom = blooms.specialize(name='blooms_custom', encode=encode)
    >>> b = blooms_custom(4)
    >>> b @= bytes([1, 2, 3])
    >>> bytes([1, 2, 3]) @ b
    True

The user of the library is responsible for ensuring that Base64-encoded Bloom filters are converted back into an an instance of the appropriate derived class.

Documentation
-------------
.. include:: toc.rst

The documentation can be generated automatically from the source files using `Sphinx <https://www.sphinx-doc.org/>`_::

    cd docs
    python -m pip install -r requirements.txt
    sphinx-apidoc -f -E --templatedir=_templates -o _source .. ../setup.py && make html

Testing and Conventions
-----------------------
All unit tests are executed and their coverage is measured when using `pytest <https://docs.pytest.org/>`_ (see ``setup.cfg`` for configuration details)::

    python -m pip install pytest pytest-cov
    python -m pytest

The subset of the unit tests included in the module itself and can be executed using `doctest <https://docs.python.org/3/library/doctest.html>`_::

    python blooms/blooms.py -v

Style conventions are enforced using `Pylint <https://www.pylint.org/>`_::

    python -m pip install pylint
    python -m pylint blooms ./test/test_blooms.py

Contributions
-------------
In order to contribute to the source code, open an issue or submit a pull request on the `GitHub page <https://github.com/nthparty/blooms>`_ for this library.

Versioning
----------
The version number format for this library and the changes to the library associated with version number increments conform with `Semantic Versioning 2.0.0 <https://semver.org/#semantic-versioning-200>`_.

Publishing
----------
This library can be published as a `package on PyPI <https://pypi.org/project/blooms/>`_ by a package maintainer. Install the `wheel <https://pypi.org/project/wheel/>`_ package, remove any old build/distribution files, and package the source into a distribution archive::

    python -m pip install wheel
    rm -rf dist *.egg-info
    python setup.py sdist bdist_wheel

Next, install the `twine <https://pypi.org/project/twine/>`_ package and upload the package distribution archive to PyPI::

    python -m pip install twine
    python -m twine upload dist/*
