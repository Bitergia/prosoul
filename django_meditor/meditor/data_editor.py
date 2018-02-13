from meditor.models import Attribute, QualityModel, Goal, Metric, Metric


class AttributesData():

    def __init__(self, state):
        self.state = state

    def __fetch_from_metrics_data(self, metrics):
        already_fetched = []

        for metric in metrics:
            attribute_name = metric.metric.attribute.name
            if attribute_name not in already_fetched:
                already_fetched.append(attribute_name)
                attribute = Attribute.objects.get(name=attribute_name)
                yield attribute

    def __fetch_from_goals(self, goals):

        for goal in goals:
            metrics = goal.metrics_data.all()
            for attribute in self.__fetch_from_metrics_data(metrics):
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
        elif self.state.metrics_data:
            metrics = Metric.objects.filter(id__in=self.state.metrics_data)
            for attribute in self.__fetch_from_metrics_data(metrics):
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
            metrics_data_iattribute = Metric.objects.filter(id__in=self.state.metrics_data).values_list("id")
            goals = Goal.objects.filter(metrics_data__in=list(metrics_data_iattribute))
            for goal in goals:
                yield goal
        elif self.state.attributes:
            attribute_iattribute = Attribute.objects.filter(name__in=self.state.attributes).values_list("id")
            repos_iattribute = Metric.objects.filter(attribute__in=list(attribute_iattribute)).values_list("id")
            metrics_data_iattribute = Metric.objects.filter(metric__in=list(repos_iattribute)).values_list("id")
            goals = Goal.objects.filter(metrics_data__in=list(metrics_data_iattribute))
            for goal in goals:
                yield goal
        elif self.state.qmodel_name:
            qmodel = QualityModel.objects.get(name=self.state.qmodel_name)
            goals = qmodel.goals.all()
            for goal in goals:
                yield goal


class MetricsData():

    def __init__(self, state=None):
        self.state = state

    def fetch(self):
        if not self.state or self.state.is_empty():
            for metric in Metric.objects.all():
                yield metric
        elif self.state.metrics_data:
            metrics_data = Metric.objects.filter(id__in=self.state.metrics_data)
            for metric in metrics_data:
                yield metric
        elif self.state.goals:
            goals = Goal.objects.filter(name__in=self.state.goals)
            for goal in goals:
                for metric in goal.metrics_data.all():
                    if self.state.attributes:
                        if metric.metric.attribute.name not in self.state.attributes:
                            continue
                    yield metric
        elif self.state.attributes:
            for metric in Metric.objects.all():
                if metric.metric.attribute.name in self.state.attributes:
                    yield metric
        elif self.state.qmodel_name:
            qmodel = QualityModel.objects.get(name=self.state.qmodel_name)
            for goal in qmodel.goals.all():
                for metric in goal.metrics_data.all():
                    yield metric
