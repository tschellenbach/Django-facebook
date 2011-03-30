#!/usr/bin/env python

import os
from distutils.core import setup
from django_facebook import __version__, __maintainer__, __email__
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

license_text = open('LICENSE.txt').read()
long_description = open('README.rest').read()

CLASSIFIERS = [
                'Development Status :: 4 - Beta',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: GNU General Public License (GPL)',
                'Natural Language :: English',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Topic :: Scientific/Engineering :: Mathematics',
                'Topic :: Software Development :: Libraries :: Python Modules'
              ]

DESCRIPTION = """Facebook open graph API client in python. Enables django applications to register users using facebook.
Fixes issues with the official but unsupported Facebook python-sdk. Enables mobile facebook authentication.
Canvas page authentication for facebook applications. FQL access via the server side api. 
"""


setup(
    name = 'django-facebook',
    version = __version__,
    url = 'http://github.com/tschellenbach/Django-facebook',
    author = __maintainer__,
    author_email = __email__,
    license = license_text,
    packages=find_packages(),
    data_files=[('', ['LICENSE.txt',
                      'README.rest'])],
    description = DESCRIPTION,
    long_description=long_description,
    classifiers = CLASSIFIERS,
    #install_requires = ('django-registration',),
)







