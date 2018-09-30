# Serializers define the API representation.

from prosoul.models import Attribute, Goal, QualityModel
from rest_framework import serializers, viewsets


class AttributeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Attribute
        fields = ('id', 'name', 'active', 'description', 'created_at', 'updated_at')
        # fields+= ('metrics', 'factoids', 'subattributes')


class GoalSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Goal
        fields = ('id', 'name', 'active', 'description', 'created_at', 'updated_at')
        # fields+= ('attributes', 'subgoals')


class QualityModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = QualityModel
        fields = ('id', 'name', 'active', 'description', 'created_at', 'updated_at')
        # fields += ('goals', )
        # fields += ('created_by', )


# ViewSets define the view behavior.
class AttributeViewSet(viewsets.ModelViewSet):
    queryset = Attribute.objects.all()
    serializer_class = AttributeSerializer


class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer


class QualityModelViewSet(viewsets.ModelViewSet):
    queryset = QualityModel.objects.all()
    serializer_class = QualityModelSerializer
