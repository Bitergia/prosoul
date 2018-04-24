#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Simple script to create the admin super user
#
# Copyright (C) 2017 Bitergia
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
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#
#

import os

import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_prosoul.settings'
django.setup()

from django.contrib.auth.management.commands.createsuperuser import get_user_model

from django_prosoul.settings import DATABASES

admin_db = list(DATABASES.keys())[0]
admin_user = 'admin'
admin_pass = 'admin'

db_manager = get_user_model()._default_manager.db_manager(admin_db)
try:
    db_manager.create_superuser(username=admin_user, email='', password=admin_pass)
    print("User for django admin created: admin/admin as login")
except django.db.utils.IntegrityError:
    print("User for django admin already exists")
