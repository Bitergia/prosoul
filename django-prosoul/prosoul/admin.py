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
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#
#

from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Attribute)
admin.site.register(models.DataSourceType)
admin.site.register(models.Factoid)
admin.site.register(models.Goal)
admin.site.register(models.Metric)
admin.site.register(models.MetricData)
admin.site.register(models.QualityModel)
