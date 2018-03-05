from prosoul.models import Attribute, QualityModel, Goal, Metric, MetricData


class AttributesData():

    def __init__(self, state):
        self.state = state

    def __find_attribute_subattributes(self, attribute):
        for subattr in attribute.subattributes.all():
            yield subattr
            for subsubattr in self.__find_attribute_subattributes(subattr):
                yield subsubattr

    def __find_goals_attributes(self, goals):
        for goal in goals:
            for attribute in goal.attributes.all():
                yield attribute
                for subattribute in self.__find_attribute_subattributes(attribute):
                    yield subattribute
            for attribute in self.__find_goals_attributes(goal.subgoals.all()):
                yield attribute

    def fetch(self):
        if not self.state or self.state.is_empty():
            attributes = Attribute.objects.all()
            for attribute in attributes:
                yield attribute
        elif self.state.attributes:
            attributes = Attribute.objects.filter(name__in=self.state.attributes)
            for attribute in attributes:
                yield attribute
        elif self.state.metrics:
            metrics = Metric.objects.filter(id__in=self.state.metrics)
            for attribute in self.__fetch_from_metrics(metrics):
                yield attribute
        elif self.state.goals:
            goals = Goal.objects.filter(name__in=self.state.goals)
            for attribute in self.__find_goals_attributes(goals):
                yield attribute
        elif self.state.qmodel_name:
            qmodel = QualityModel.objects.get(name=self.state.qmodel_name)
            goals = qmodel.goals.all()
            for attribute in self.__find_goals_attributes(goals):
                yield attribute


class QualityModelsData():

    def __init__(self, state=None):
        self.state = state

    def fetch(self):
        for qmodel in QualityModel.objects.all():
            yield qmodel


class GoalsData():

    def __init__(self, state):
        self.state = state

    def fetch(self):
        if not self.state or self.state.is_empty():
            for goal in Goal.objects.all():
                yield goal
        elif self.state.goals:
            goals = Goal.objects.filter(name__in=self.state.goals)
            for goal in goals:
                yield goal
        elif self.state.attributes:
            attributes = Attribute.objects.filter(name__in=self.state.attributes).values_list("id")
            goals = Goal.objects.filter(attributes__in=list(attributes))
            for goal in goals:
                yield goal
        elif self.state.metrics:
            metrics = Metric.objects.filter(id__in=self.state.metrics).values_list("id")
            attributes = Attribute.objects.filter(metrics__in=list(metrics)).values_list("id")
            goals = Goal.objects.filter(attributes__in=list(attributes))
            for goal in goals:
                yield goal
        elif self.state.qmodel_name:
            qmodel = QualityModel.objects.get(name=self.state.qmodel_name)
            goals = qmodel.goals.all()
            for goal in goals:
                yield goal
                for subgoal in goal.subgoals.all():
                    yield subgoal


class MetricsData():

    def __init__(self, state=None):
        self.state = state

    def __find_goals_metrics(self, goals):
        for goal in goals:
            for attribute in goal.attributes.all():
                for metric in attribute.metrics.all():
                    yield metric
            for metric in self.__find_goals_metrics(goal.subgoals.all()):
                yield metric

    def fetch(self):
        if not self.state or self.state.is_empty():
            for metric in Metric.objects.all():
                yield metric
        elif self.state.metrics:
            metrics = Metric.objects.filter(id__in=self.state.metrics)
            for metric in metrics:
                yield metric
        elif self.state.attributes:
            attributes = Attribute.objects.filter(name__in=self.state.attributes)
            for attribute in attributes:
                for metric in attribute.metrics.all():
                    yield metric
        elif self.state.goals:
            goals = Goal.objects.filter(name__in=self.state.goals)
            for metric in self.__find_goals_metrics(goals):
                yield metric
        elif self.state.qmodel_name:
            qmodel = QualityModel.objects.get(name=self.state.qmodel_name)
            for metric in self.__find_goals_metrics(qmodel.goals.all()):
                yield metric


class MetricsDataData():

    def __init__(self, state=None):
        self.state = state

    def fetch(self):
        for metric_data in MetricData.objects.all():
            yield metric_data
