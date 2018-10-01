# Serializers define the API representation.

from django.contrib.auth.models import User

from prosoul.models import Attribute, DataSourceType, Factoid, Goal, Metric, MetricData, QualityModel
from rest_framework import serializers, viewsets


PROSOUL_FIELDS = ('id', 'name', 'active', 'description', 'created_at', 'updated_at')


class AttributeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Attribute
        fields = PROSOUL_FIELDS
        # fields+= ('metrics', 'factoids', 'subattributes')


class DataSourceTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataSourceType
        fields = PROSOUL_FIELDS
        # fields+= ('', )


class FactoidSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Factoid
        fields = PROSOUL_FIELDS
        # fields+= ('', )


class GoalSerializer(serializers.HyperlinkedModelSerializer):
    attributes = AttributeSerializer(many=True)
    # subgoals = GoalSerializer(many=True)
    class Meta:
        model = Goal
        fields = PROSOUL_FIELDS
        fields += ('attributes', )
        # fields+= ('attributes', 'subgoals')


class MetricSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Metric
        fields = PROSOUL_FIELDS
        # fields+= ('', )


class MetricDataSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MetricData
        fields = tuple(f for f in PROSOUL_FIELDS if f != 'name')
        # fields+= ('', )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class QualityModelSerializer(serializers.HyperlinkedModelSerializer):
    created_by = UserSerializer()
    goals = GoalSerializer(many=True)

    class Meta:
        model = QualityModel
        fields = PROSOUL_FIELDS
        fields += ('goals', )
        fields += ('created_by', )



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
