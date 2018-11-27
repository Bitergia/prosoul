#!/usr/bin/env python3

# -*- coding: utf-8 -*-
#
# Simple script to modify the Django settings to deploy:
#   SECRET_KEY in a django project
#   DEBUG = False
#   ALLOWED_HOSTS = ['*']
#
# Copyright (C) 2018 Bitergia
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Valerio Cosentino <valcos@bitergia.com>
#
#

import os

settings_file = 'django_prosoul/settings.py'
settings = None

try:
    allowed_hosts = os.environ['ALLOWED_HOSTS'].split(" ")
except KeyError:
    allowed_hosts = []

with open(settings_file) as f:
    settings = f.read()
    settings = settings.replace("DEBUG = True", "DEBUG = False")
    settings = settings.replace("ALLOWED_HOSTS = []", "ALLOWED_HOSTS = {}".format(str(allowed_hosts)))

with open(settings_file, "w") as f:
    f.write(settings)

print("Django configured for deployment (debug, allowed_hosts) in", settings_file)
