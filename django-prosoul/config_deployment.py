#!/usr/bin/env python3

# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Bitergia
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
