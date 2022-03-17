from setuptools import setup

with open("README.rst", "r") as fh:
    long_description = fh.read().replace(".. include:: toc.rst\n\n", "")

# The lines below can be parsed by `docs/conf.py`.
name = "blooms"
version = "1.1.0"

setup(
    name=name,
    version=version,
    packages=[name,],
    install_requires=[],
    license="MIT",
    url="https://github.com/nthparty/blooms",
    author="Andrei Lapets",
    author_email="a@lapets.io",
    description="Lightweight Bloom filter data structure derived "+\
                "from the built-in bytearray type.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
)
