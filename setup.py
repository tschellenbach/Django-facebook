#!/usr/bin/env python
from distutils.core import setup
import django_facebook

LONG_DESCRIPTION = """Facebook open graph API auth backend implementation using 
the Django web framework and python."""

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

KEYWORDS = 'color math conversions'

setup(name='django-facebook',
      version=django_facebook.VERSION,
      description='Facebook Open graph API auth backend for Django..',
      long_description = LONG_DESCRIPTION,
      author='Thierry Schellenbach',
      url='http://github.com/tschellenbach/Django-facebook',
      packages=['django_facebook'],
      platforms = ['Platform Independent'],
      license = 'GPLv3',
      classifiers = CLASSIFIERS,
      keywords = KEYWORDS,
      requires = ['django-registration']
     )
