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

# Serializers define the API representation.

from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator

from prosoul.models import Attribute, DataSourceType, Factoid, Goal, Metric, MetricData, QualityModel
from rest_framework import serializers, viewsets


PROSOUL_FIELDS = ('id', 'name', 'active', 'description', 'created_at', 'updated_at', 'created_by')
PROSOUL_FIELDS_UPDATE = ('name', 'active', 'description')  # Fields updated


class MetaNameMixin():
    # In POST operations which include a list of object names to be included
    # those names must not be unique because they already exist, so removing this validator.
    # This can bite us when creating new objects, where this validator is useful!

    # https://medium.com/django-rest-framework/dealing-with-unique-constraints-in-nested-serializers-dade33b831d9
    extra_kwargs = {
        'name': {
            'validators': [UnicodeUsernameValidator()],
        }
    }


class CreateUpdateNestedMixin():
    """
    Mixin used to implement the persistence of nested objects
    """

    class Meta():
        nested_fields = []  # Fields with nested objects
        nested_fields_model = []  # Mapping between fields and the nested object model

    def extract_nested_objects_data(self, validated_data):
        """
        Extract the data for nested objects from validated_data

        :param validated_data: data received by HTTP protocol already validated
        :return: a dict with the nested object field as key and a the list of nested objects data as value
        """

        related_objects_data = {}
        for field in self.Meta.nested_fields:
            related_objects_data[field] = None
            if field in validated_data:
                field_data = validated_data.pop(field)
                related_objects_data[field] = field_data

        return related_objects_data

    def update_nested_objects(self, instance, nested_objects_data):
        """
        Add to the instance object fields the nested objects

        :param instance: an object model instance in which to add the nested objects (i.e. Attribute instance)
        :param nested_objects_data: a dict with the fields and their nested objects data needed to find the objects.
        For each field in the dict there is a list of nested objects data.
        :return:
        """

        for field in nested_objects_data:
            if nested_objects_data[field] is None:
                # It could be a list or a single value
                try:
                    setattr(instance, field, None)
                except TypeError:
                    getattr(instance, field).set([])

                continue

            if not isinstance(nested_objects_data[field], list):
                nested_object = None
                if nested_objects_data[field]:
                    nested_object = self.Meta.nested_fields_model[field].objects.get(**nested_objects_data[field])
                setattr(instance, field, nested_object)
            else:
                # Empty the nested objects for this field (i.e. Attribute.metrics.set([])
                getattr(instance, field).set([])
                if nested_objects_data[field]:
                    for object_data in nested_objects_data[field]:
                        # Create the object model from the data
                        object = self.Meta.nested_fields_model[field].objects.get(**object_data)
                        getattr(instance, field).add(object)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['username']


class MetricDataSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta(MetaNameMixin):
        model = MetricData
        fields = tuple(f for f in PROSOUL_FIELDS if f != 'name')
        fields += ('implementation', 'params')

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]
        metric_data = MetricData.objects.create(created_by=user, **validated_data)
        return metric_data

    def update(self, instance, validated_data):
        for field in ['active', 'description', 'implementation', 'params']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        return instance


class DataSourceTypeSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta(MetaNameMixin):
        model = DataSourceType
        fields = PROSOUL_FIELDS

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]
        data_source_type = DataSourceType.objects.create(created_by=user, **validated_data)
        return data_source_type

    def update(self, instance, validated_data):
        for field in PROSOUL_FIELDS:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        return instance


class MetricSerializer(serializers.HyperlinkedModelSerializer, CreateUpdateNestedMixin):
    created_by = UserSerializer(read_only=True)
    data = MetricDataSerializer(required=False)
    data_source_type = DataSourceTypeSerializer(required=False)

    class Meta(MetaNameMixin):
        model = Metric
        fields = PROSOUL_FIELDS + ('thresholds', )
        nested_fields = ('data', 'data_source_type', )
        nested_fields_model = {"data": MetricData, "data_source_type": DataSourceType}
        fields += nested_fields

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]

        nested_objects_data = self.extract_nested_objects_data(validated_data)
        metric = Metric.objects.create(created_by=user, **validated_data)
        self.update_nested_objects(metric, nested_objects_data)

        return metric

    def update(self, instance, validated_data):
        for field in PROSOUL_FIELDS_UPDATE + ('thresholds',):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        nested_objects_data = self.extract_nested_objects_data(validated_data)
        self.update_nested_objects(instance, nested_objects_data)

        instance.save()

        return instance


class FactoidSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)
    data_source_type = DataSourceTypeSerializer(required=False)

    class Meta(MetaNameMixin):
        model = Factoid
        fields = PROSOUL_FIELDS
        fields += ('data_source_type', )

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]
        ds = None
        if 'data_source_type' in validated_data:
            ds_data = validated_data.pop('data_source_type')
            ds = DataSourceType.objects.get(**ds_data)
        # Create the metric object
        factoid = Factoid.objects.create(created_by=user, data_source_type=ds, **validated_data)
        return factoid

    def update(self, instance, validated_data):
        for field in PROSOUL_FIELDS_UPDATE:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        if 'data_source_type' in validated_data:
            ds_data = validated_data.pop('data_source_type')
            ds = DataSourceType.objects.get(**ds_data)
            instance.data_source_type = ds

        instance.save()

        return instance


class SubAttributeSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)
    metrics = MetricSerializer(many=True, required=False)
    factoids = FactoidSerializer(many=True, required=False)

    class Meta(MetaNameMixin):
        model = Attribute
        fields = PROSOUL_FIELDS
        fields += ('metrics', 'factoids')


class AttributeSerializer(serializers.HyperlinkedModelSerializer, CreateUpdateNestedMixin):
    created_by = UserSerializer(read_only=True)
    metrics = MetricSerializer(many=True, required=False)
    factoids = FactoidSerializer(many=True, required=False)
    subattributes = SubAttributeSerializer(many=True, required=False)

    class Meta(MetaNameMixin):
        model = Attribute

        nested_fields = ('metrics', 'factoids', 'subattributes')
        nested_fields_model = {"metrics": Metric, "factoids": Factoid, "subattributes": Attribute}
        fields = PROSOUL_FIELDS
        fields += nested_fields

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]

        nested_objects_data = self.extract_nested_objects_data(validated_data)

        attribute = Attribute.objects.create(created_by=user, **validated_data)

        self.update_nested_objects(attribute, nested_objects_data)

        return attribute

    def update(self, instance, validated_data):
        for field in PROSOUL_FIELDS_UPDATE:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        nested_objects_data = self.extract_nested_objects_data(validated_data)
        self.update_nested_objects(instance, nested_objects_data)

        instance.save()

        return instance


class SubGoalSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True, required=False)

    attributes = AttributeSerializer(many=True, required=False)

    class Meta(MetaNameMixin):
        model = Goal
        fields = PROSOUL_FIELDS
        fields += ('attributes', )


class GoalSerializer(serializers.HyperlinkedModelSerializer, CreateUpdateNestedMixin):
    created_by = UserSerializer(read_only=True)

    attributes = AttributeSerializer(many=True, required=False)
    subgoals = SubGoalSerializer(many=True, required=False)

    class Meta(MetaNameMixin):
        model = Goal
        fields = PROSOUL_FIELDS
        nested_fields = ('attributes', 'subgoals')
        nested_fields_model = {"attributes": Attribute, "subgoals": Goal}
        fields += nested_fields

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]

        nested_objects_data = self.extract_nested_objects_data(validated_data)

        goal = Goal.objects.create(created_by=user, **validated_data)

        self.update_nested_objects(goal, nested_objects_data)

        return goal

    def update(self, instance, validated_data):
        for field in PROSOUL_FIELDS_UPDATE:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        nested_objects_data = self.extract_nested_objects_data(validated_data)
        self.update_nested_objects(instance, nested_objects_data)

        instance.save()

        return instance


class QualityModelSerializer(serializers.HyperlinkedModelSerializer, CreateUpdateNestedMixin):
    created_by = UserSerializer(read_only=True)
    goals = GoalSerializer(many=True)

    class Meta(MetaNameMixin):
        model = QualityModel
        fields = PROSOUL_FIELDS
        nested_fields = ('goals',)
        nested_fields_model = {"goals": Goal}
        fields += nested_fields

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]

        nested_objects_data = self.extract_nested_objects_data(validated_data)

        quality_model = QualityModel.objects.create(created_by=user, **validated_data)

        self.update_nested_objects(quality_model, nested_objects_data)

        return quality_model

    def update(self, instance, validated_data):
        for field in PROSOUL_FIELDS_UPDATE:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        nested_objects_data = self.extract_nested_objects_data(validated_data)
        self.update_nested_objects(instance, nested_objects_data)

        instance.save()

        return instance


# ViewSets define the view behavior.
class AttributeViewSet(viewsets.ModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer


class DataSourceTypeViewSet(viewsets.ModelViewSet):
    queryset = DataSourceType.objects.all()
    serializer_class = DataSourceTypeSerializer


class FactoidViewSet(viewsets.ModelViewSet):
    queryset = Factoid.objects.all()
    serializer_class = FactoidSerializer


class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer


class MetricViewSet(viewsets.ModelViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer


class MetricDataViewSet(viewsets.ModelViewSet):
    queryset = MetricData.objects.all()
    serializer_class = MetricDataSerializer


class QualityModelViewSet(viewsets.ModelViewSet):
    queryset = QualityModel.objects.all()
    serializer_class = QualityModelSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
