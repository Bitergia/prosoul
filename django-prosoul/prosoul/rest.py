# Serializers define the API representation.

from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator

from prosoul.models import Attribute, DataSourceType, Factoid, Goal, Metric, MetricData, QualityModel
from rest_framework import serializers, viewsets


PROSOUL_FIELDS = ('id', 'name', 'active', 'description', 'created_at', 'updated_at', 'created_by')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['username']
        # https://medium.com/django-rest-framework/dealing-with-unique-constraints-in-nested-serializers-dade33b831d9
        extra_kwargs = {
            'username': {
                'validators': [UnicodeUsernameValidator()],
            }
        }


class MetricDataSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = MetricData
        fields = tuple(f for f in PROSOUL_FIELDS if f != 'name')
        fields += ('id', 'implementation', 'params')

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

    class Meta:
        model = DataSourceType
        fields = PROSOUL_FIELDS

        # https://medium.com/django-rest-framework/dealing-with-unique-constraints-in-nested-serializers-dade33b831d9
        extra_kwargs = {
            'name': {
                'validators': [UnicodeUsernameValidator()],
            }
        }

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]
        data_source_type = DataSourceType.objects.create(created_by=user, **validated_data)
        return data_source_type

    def update(self, instance, validated_data):
        for field in ['active', 'description', 'name']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        return instance


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)
    data = MetricDataSerializer(required=False)
    data_source_type = DataSourceTypeSerializer(required=False)

    class Meta:
        model = Metric
        fields = PROSOUL_FIELDS
        fields += ('data', 'data_source_type', 'thresholds')

    def create(self, validated_data):
        username = self.context['request'].user.username
        user = User.objects.get_or_create(username=username)[0]
        # extract metric data
        metric_data = None
        if 'data' in validated_data:
            metric_data_data = validated_data.pop('data')
            metric_data = MetricData.objects.get(**metric_data_data)
        # extract data source type data
        ds = None
        if 'data_source_type' in validated_data:
            ds_data = validated_data.pop('data_source_type')
            ds = DataSourceType.objects.get(**ds_data)
        # Create the metric object
        metric = Metric.objects.create(created_by=user, data=metric_data, data_source_type=ds, **validated_data)
        return metric

    def update(self, instance, validated_data):
        for field in ['active', 'description', 'name', 'thresholds']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        # extract metric data
        if 'data' in validated_data:
            metric_data_data = validated_data.pop('data')
            metric_data = MetricData.objects.get(**metric_data_data)
            instance.data = metric_data
        if 'data_source_type' in validated_data:
            ds_data = validated_data.pop('data_source_type')
            ds = DataSourceType.objects.get(**ds_data)
            instance.data_source_type = ds

        instance.save()

        return instance


class FactoidSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)
    data_source_type = DataSourceTypeSerializer(required=False)

    class Meta:
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
        for field in ['active', 'description', 'name']:
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
    metrics = MetricSerializer(many=True)
    factoids = FactoidSerializer(many=True)

    class Meta:
        model = Attribute
        fields = PROSOUL_FIELDS
        fields += ('metrics', 'factoids')


class AttributeSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)
    metrics = MetricSerializer(many=True)
    factoids = FactoidSerializer(many=True)
    subattributes = SubAttributeSerializer(many=True)

    class Meta:
        model = Attribute
        fields = PROSOUL_FIELDS
        fields += ('metrics', 'factoids', 'subattributes')


class SubGoalSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)

    attributes = AttributeSerializer(many=True)

    class Meta:
        model = Goal
        fields = PROSOUL_FIELDS
        fields += ('attributes', )


class GoalSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)

    attributes = AttributeSerializer(many=True)
    # subgoals = SubGoalSerializer(many=True)

    class Meta:
        model = Goal
        fields = PROSOUL_FIELDS
        fields += ('attributes', )
        # fields += ('attributes', 'subgoals', )

    def create(self, validated_data):
        user_data = validated_data.pop('created_by')
        user = User.objects.get_or_create(username=user_data['username'])[0]
        goal = Goal.objects.create(created_by=user, **validated_data)
        return goal


class QualityModelSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer(read_only=True)
    goals = GoalSerializer(many=True)

    class Meta:
        model = QualityModel
        fields = PROSOUL_FIELDS
        fields += ('goals', )

    def create(self, validated_data):
        user_data = validated_data.pop('created_by')
        user = User.objects.get_or_create(username=user_data['username'])[0]
        quality_model = QualityModel.objects.create(created_by=user, **validated_data)
        return quality_model


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
