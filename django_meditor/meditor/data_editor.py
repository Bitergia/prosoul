from meditor.models import Attribute, QualityModel, Goal, Metric, MetricData
from grimoire_elk import utils as gelk_utils


class AttributesData():

    def __init__(self, state):
        self.state = state

    def __fetch_from_metrics_data(self, views):
        already_fetched = []

        for view in views:
            attribute_name = view.metric.attribute.name
            if attribute_name not in already_fetched:
                already_fetched.append(attribute_name)
                attribute = Attribute.objects.get(name=attribute_name)
                yield attribute

    def __fetch_from_goals(self, goals):

        for goal in goals:
            views = goal.metrics_data.all()
            for attribute in self.__fetch_from_metrics_data(views):
                yield attribute

    def fetch(self):

        if not self.state or self.state.is_empty():
            supported_attributes = list(gelk_utils.get_connectors())
            for attribute_name in supported_attributes:
                attribute = Attribute(name=attribute_name)
                yield attribute
        elif self.state.attributes:
            attributes = Attribute.objects.filter(name__in=self.state.attributes)
            for attribute in attributes:
                yield attribute
        elif self.state.metrics_data:
            views = MetricData.objects.filter(id__in=self.state.metrics_data)
            for attribute in self.__fetch_from_metrics_data(views):
                yield attribute
        elif self.state.goals:
            goals = Goal.objects.filter(name__in=self.state.goals)
            for attribute in self.__fetch_from_goals(goals):
                yield attribute
        elif self.state.qmodel_name:
            qmodel = QualityModel.objects.get(name=self.state.qmodel_name)
            goals = qmodel.goals.all()
            for attribute in self.__fetch_from_goals(goals):
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
        elif self.state.metrics_data:
            metrics_data_iattribute = MetricData.objects.filter(id__in=self.state.metrics_data).values_list("id")
            goals = Goal.objects.filter(metrics_data__in=list(metrics_data_iattribute))
            for goal in goals:
                yield goal
        elif self.state.attributes:
            attribute_iattribute = Attribute.objects.filter(name__in=self.state.attributes).values_list("id")
            repos_iattribute = Metric.objects.filter(attribute__in=list(attribute_iattribute)).values_list("id")
            metrics_data_iattribute = MetricData.objects.filter(metric__in=list(repos_iattribute)).values_list("id")
            goals = Goal.objects.filter(metrics_data__in=list(metrics_data_iattribute))
            for goal in goals:
                yield goal
        elif self.state.qmodel_name:
            qmodel = QualityModel.objects.get(name=self.state.qmodel_name)
            goals = qmodel.goals.all()
            for goal in goals:
                yield goal


class MetricDatasData():

    def __init__(self, state=None):
        self.state = state

    def fetch(self):
        if not self.state or self.state.is_empty():
            for view in MetricData.objects.all():
                yield view
        elif self.state.metrics_data:
            metrics_data = MetricData.objects.filter(id__in=self.state.metrics_data)
            for view in metrics_data:
                yield view
        elif self.state.goals:
            goals = Goal.objects.filter(name__in=self.state.goals)
            for goal in goals:
                for view in goal.metrics_data.all():
                    if self.state.attributes:
                        if view.metric.attribute.name not in self.state.attributes:
                            continue
                    yield view
        elif self.state.attributes:
            for view in MetricData.objects.all():
                if view.metric.attribute.name in self.state.attributes:
                    yield view
        elif self.state.qmodel_name:
            qmodel = QualityModel.objects.get(name=self.state.qmodel_name)
            for goal in qmodel.goals.all():
                for view in goal.metrics_data.all():
                    yield view
