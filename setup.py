from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="gpr",
    version="0.1.0",
    author="Ilija Medan",
    author_email="medan@astro.gsu.edu",
    description="Photometric Metallicity Relationship for K and M Dwarfs",
    long_description=read('README.md'),
    license="BSD 3-Clause",
    py_modules=['gpr.gpr']
    # classifiers=[]
)
