#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Alvaro del Castillo <acs@bitergia.com>
#

import codecs
import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
readme_md = os.path.join(here, 'README.md')

# Get the package description from the README.md file
with codecs.open(readme_md, encoding='utf-8') as f:
    long_description = f.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-prosoul',
    version='0.4.0',
    packages=['prosoul'],
    include_package_data=True,
    license='GPLv3',
    description='Prosoul is a software quality models manager to create, import/export, view and edit models',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/bitergia/prosoul',
    author='Bitergia',
    author_email='acs@bitergia.com',
    keywords="development repositories analytics quality models assessment visualization",
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Customer Service',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'django>=2.0',
        'matplotlib',
        'grimoire-elk',
        'sortinghat',
        'kidash',
        'djangorestframework',
        'grimoirelab-toolkit'
    ],
    python_requires='>=3.4'

)
