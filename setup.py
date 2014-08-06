#!/usr/bin/env python

from distutils.core import setup

setup(name='django_hana_odbc',
      version='1.0',
      description='SAP HANA backend for Django 1.5',
      author='MTR Design',
      author_email='office@mtr-design.co.uk',
      url='https://github.com/mtrdesign/django_hana_odbc',
      packages=['django_hana_odbc'],
      requires = ['django (>= 1.5)'],
     )
