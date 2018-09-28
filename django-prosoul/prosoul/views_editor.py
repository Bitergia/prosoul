import functools
import json

from datetime import datetime
from time import time

from django import shortcuts
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404

from django.http import HttpResponse
from django.template import loader

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from django.db.utils import IntegrityError

from django.views import View

from prosoul.prosoul_export import fetch_models
from prosoul.prosoul_import import convert_to_grimoirelab, feed_models, SUPPORTED_FORMATS
from prosoul.models import Attribute, Goal, Metric, MetricData, QualityModel

from . import forms_editor


#
# Logic not moved inside classes yet
#

def perfdata(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        task_init = time()
        data = func(*args, **kwargs)
        print("%s: %0.3f sec" % (func, time() - task_init))
        return data
    return decorator


@perfdata
def build_forms_context(state=None):
    """ Get all forms to be shown in the editor """
    qmodel_form = forms_editor.QualityModelsForm(state=state)
    add_qmodel_form = forms_editor.QualityModelForm(state=state)
    goals_form = forms_editor.GoalsForm(state=state)
    goal_form = forms_editor.GoalForm(state=state)
    goal_remove_form = forms_editor.GoalForm(state=state)
    attributes_form = forms_editor.AttributesForm(state=state)
    attribute_form = forms_editor.AttributeForm(state=state)
    attribute_remove_form = forms_editor.AttributeForm(state=state)
    metrics_form = forms_editor.MetricsForm(state=state)
    metric_form = forms_editor.MetricForm(state=state)
    metric_data_form = forms_editor.MetricDataForm(state=state)

    if state:
        if state.qmodel_id:
            qmodel_form.initial['id'] = state.qmodel_id
            qmodel_form.initial['name'] = QualityModel.objects.get(id=state.qmodel_id).name
        if state.goals:
            goals_form.initial['id'] = state.goals[0]
            goal_name = Goal.objects.get(id=state.goals[0]).name
            goals_form.initial['name'] = goal_name
            goal_form.initial['goal_name'] = goal_name
            goal_remove_form.initial['goal_name'] = state.goals[0]
        if state.attributes:
            attributes_form.initial['id'] = state.attributes[0]
            attr_name = Attribute.objects.get(id=state.attributes[0]).name
            attributes_form.initial['name'] = attr_name
            attribute_form.initial['attribute_name'] = attr_name
            attribute_remove_form.initial['attribute_name'] = attr_name
        if state.metrics:
            metrics_form.initial['id'] = state.metrics[0]
            metric_name = Metric.objects.get(id=state.metrics[0]).name
            metrics_form.initial['name'] = metric_name
            attribute_form.initial['metric_id'] = state.metrics[0]

    context = {"qmodels_form": qmodel_form,
               "qmodel_form": add_qmodel_form,
               "goals_form": goals_form,
               "goal_form": goal_form,
               "goal_remove_form": goal_remove_form,
               "attributes_form": attributes_form,
               "attribute_form": attribute_form,
               "attribute_remove_form": attribute_remove_form,
               "metrics_form": metrics_form,
               "metric_form": metric_form,
               "metric_data_form": metric_data_form
               }
    context['active_page'] = 'editor'
    return context


def import_from_file(request):

    if request.method == "POST":
        myfile = request.FILES["imported_file"]
        cur_dt = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        file_name = "%s_%s.json" % (myfile, cur_dt)
        fpath = '.imported/' + file_name  # FIXME Define path where all these files must be saved
        save_path = default_storage.save(fpath, ContentFile(myfile.read()))

        task_init = time()

        with open(save_path) as fmodel:
            models_json = {}
            import_models_json = json.load(fmodel)

            # Detect the format automatically
            for fmt in SUPPORTED_FORMATS:
                try:
                    models_json = convert_to_grimoirelab(fmt, import_models_json)
                except Exception as ex:
                    print("%s is not in format %s" % (myfile, fmt))
                    continue

                try:
                    feed_models(models_json)
                    break
                except Exception as ex:
                    pass

            if not models_json:
                raise RuntimeError("File %s couldn't be imported." % myfile.name)

        print("Total loading time ... %.2f sec", time() - task_init)

    return shortcuts.redirect("/")


def export_to_file(request, qmodel=None):

    if (request.method == "GET") and (not qmodel):
        return shortcuts.redirect("prosoul:editor")

    if request.method == "POST":
        qmodel_id = request.POST["id"]
        qmodel = QualityModel.objects.get(id=qmodel_id)

    file_name = "qmodel_%s.json" % qmodel
    task_init = time()
    try:
        models_json = fetch_models(qmodel)
    except (QualityModel.DoesNotExist, Exception) as ex:
        print(ex)
        error_msg = "Goals from qmodel \"%s\" couldn't be exported." % qmodel
        if request.method == "POST":
            # If request comes from web UI and fails, return error page
            return return_error(error_msg)
        else:
            # If request comes as a GET request, return HTTP 404: Not Found
            return HttpResponse(status=404)

    print("Total loading time ... %.2f sec", time() - task_init)
    if models_json:
        models = json.dumps(models_json, indent=True, sort_keys=True)
        response = HttpResponse(models, content_type="application/json")
        response['Content-Disposition'] = 'attachment; filename=' + file_name
        return response
    else:
        error_msg = "There are no goals to export"
        return return_error(error_msg)

    return editor(request)


def return_error(message):

    template = loader.get_template('prosoul/error.html')
    context = {"alert_message": message}
    render_error = template.render(context)
    return HttpResponse(render_error)

#
# Classes implementing the logic
#


class EditorState():

    def __init__(self, qmodel_id=None, goals=None, attributes=None,
                 metrics=None, form=None):
        self.qmodel_id = qmodel_id
        self.goals = goals
        self.attributes = attributes
        self.metrics = metrics

        if form:
            # The form includes the state not changed to be propagated
            qmodels_state = form.cleaned_data['qmodel_state']
            goals_state = form.cleaned_data['goals_state']
            attributes = form.cleaned_data['attributes_state']
            metrics = form.cleaned_data['metrics_state']

            if self.qmodel_id is None:
                self.qmodel_id = qmodels_state if qmodels_state else None
            if self.goals is None:
                self.goals = [goals_state] if goals_state else []
            if self.attributes is None:
                self.attributes = [attributes] if attributes else []
            if self.metrics is None:
                self.metrics = [metrics] if metrics else []

    def is_empty(self):
        return not (self.qmodel_id or self.goals or self.attributes or self.metrics)

    def initial_state(self):
        """ State to be filled in the forms so it is propagated

        The state needs to be serialized so it can be used in
        forms fields.
        """
        initial = {}

        initial['qmodel_state'] = self.qmodel_id

        if self.goals:
            initial['goals_state'] = ";".join([str(oid) for oid in self.goals])
        else:
            initial['goals_state'] = None

        if self.attributes:
            initial['attributes_state'] = ";".join([str(oid) for oid in self.attributes])
        else:
            initial['attributes_state'] = None

        if self.metrics:
            initial['metrics_state'] = ";".join([str(oid) for oid in self.metrics])
        else:
            initial['metrics_state'] = None

        return initial


# Login for Views

class JustPostMixin():
    """
    Mixin to add the support only for HTTP Post requests and to execute the action configured
    """

    http_method_names = ['post']

    action = None

    def post(self, request):
        return self.action(request)


class EditorView(LoginRequiredMixin, View):

    http_method_names = ['get']

    @perfdata
    def get(self, request):
        """ Shows the Prosoul Editor """

        context = build_forms_context()

        return shortcuts.render(request, 'prosoul/editor.html', context)


class QualityModelView(LoginRequiredMixin, JustPostMixin, View):

    @staticmethod
    def select_qmodel(request, context=None):
        template = "prosoul/editor.html"
        form = forms_editor.QualityModelsForm(request.POST)
        if form.is_valid():
            model_id = form.cleaned_data['id']
            if not model_id:
                return shortcuts.render(request, template, build_forms_context())
            # Select and qmodel reset the state. Don't pass form=form
            state = build_forms_context(EditorState(qmodel_id=model_id))
            if context:
                context.update(state)
            else:
                context = state
            return shortcuts.render(request, template, context)
        else:
            # Ignore when the empty option is selected
            return shortcuts.render(request, template, build_forms_context())

    @staticmethod
    def add_qmodel(request):
        form = forms_editor.QualityModelForm(request.POST)
        if form.is_valid():
            qmodel_name = form.cleaned_data['qmodel_name']

            try:
                qmodel_orm = QualityModel.objects.get(name=qmodel_name)
            except QualityModel.DoesNotExist:
                qmodel_orm = QualityModel(name=qmodel_name)
                qmodel_orm.save()

            # Select and qmodel reset the state. Don't pass form=form
            return shortcuts.render(request, 'prosoul/editor.html',
                                    build_forms_context(EditorState(qmodel_id=qmodel_orm.id)))
        else:
            # TODO: Show error
            raise Http404

    @staticmethod
    def remove_qmodel(request):
        errors = None
        form = forms_editor.QualityModelForm(request.POST)
        if form.is_valid():
            qmodel_name = form.cleaned_data['qmodel_name']
            try:
                QualityModel.objects.get(name=qmodel_name).delete()
            except QualityModel.DoesNotExist:
                errors = "Can't delete not found quality model %s" % qmodel_name
        else:
            error = form.errors

        # Select and qmodel reset the state. Don't pass form=form
        context = build_forms_context(EditorState(qmodel_id=None))
        context['errors'] = errors

        return shortcuts.render(request, 'prosoul/editor.html', context)


    @staticmethod
    def update_qmodel(request):
        errors = None
        form = forms_editor.QualityModelForm(request.POST)
        if form.is_valid():
            qmodel_id = form.cleaned_data['qmodel_state']
            qmodel_name = form.cleaned_data['qmodel_name']
            try:
                qmodel_orm = QualityModel.objects.get(id=qmodel_id)
                qmodel_orm.name = qmodel_name
                qmodel_orm.save()
            except QualityModel.DoesNotExist:
                errors = "Can't find quality model %s" % qmodel_id
        else:
            error = form.errors

        context = build_forms_context(EditorState(form=form))
        context['errors'] = errors

        return shortcuts.render(request, 'prosoul/editor.html', context)


class MetricDataView(LoginRequiredMixin, JustPostMixin, View):

    @staticmethod
    def add_metric_data(request):
        form = forms_editor.MetricDataForm(request.POST)
        if form.is_valid():
            state = EditorState(form=form)
            metric_id = state.metrics[0]
            implementation = form.cleaned_data['implementation']
            params = form.cleaned_data['params']

            # Try to find a metric data already created
            try:
                metric_data_orm = MetricData.objects.get(implementation=implementation, params=params)
            except MetricData.DoesNotExist:
                # Create a new metric
                metric_data_orm = MetricData(implementation=implementation, params=params)
                metric_data_orm.save()

            metric_orm = Metric.objects.get(id=metric_id)
            metric_orm.data = metric_data_orm
            metric_orm.save()

            # form.cleaned_data['metrics_state'] = []
            state = EditorState(form=form)
            return shortcuts.render(request, 'prosoul/editor.html',
                                    build_forms_context(state))
        else:
            # TODO: Show error
            print(form.errors)
            raise Http404


class MetricView(LoginRequiredMixin, JustPostMixin, View):

    @staticmethod
    def add_metric(request):
        error = None
        form = forms_editor.MetricForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['metric_name']
            thresholds = form.cleaned_data['metric_thresholds']
            attribute_id = form.cleaned_data['attributes']

            attribute_orm = Attribute.objects.get(id=attribute_id)

            # Try to find a metric already created
            try:
                metric_orm = Metric.objects.get(name=name)
                error = "The metric %s already exists" % name
                # metric_orm.attribute = attribute_orm
                # metric_orm.thresholds = thresholds
            except Metric.DoesNotExist:
                # Create a new metric
                metric_orm = Metric(name=name, attribute=attribute_orm,
                                    thresholds=thresholds)

            metric_orm.save()

            attribute_orm.metrics.add(metric_orm)
            attribute_orm.save()
        else:
            error = form.errors

        form.cleaned_data['metrics_state'] = []
        state = EditorState(form=form)
        context = build_forms_context(state)
        context.update({"errors": error})

        return shortcuts.render(request, 'prosoul/editor.html',
                                context)


    @staticmethod
    def remove_metric(request):
        form = forms_editor.MetricForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['metric_id']:
                metric_id = int(form.cleaned_data['metric_id'])
                Metric.objects.get(id=metric_id).delete()
            # Clean from the state the removed metric view
            form.cleaned_data['metrics_state'] = []
            return shortcuts.render(request, 'prosoul/editor.html',
                                    build_forms_context(EditorState(form=form)))
        else:
            # TODO: Show error
            print(form.errors)
            raise Http404


    @staticmethod
    def select_metric(request):
        error = None
        template = 'prosoul/editor.html'
        form = forms_editor.MetricsForm(request.POST)
        if form.is_valid():
            metric_id = int(form.cleaned_data['id'])
            metrics = [metric_id]
            old_metrics = form.cleaned_data['metrics_state']
            if old_metrics == str(metric_id):
                # Unselect the metric
                form.cleaned_data['metrics_state'] = None
                metrics = None

            state = EditorState(form=form, metrics=metrics)
        else:
            state = EditorState(form=form)
            error = form.errors

        context = build_forms_context(state)
        context.update({"errors": error})
        return shortcuts.render(request, template, context)


    @staticmethod
    def update_metric(request):
        form = forms_editor.MetricForm(request.POST)

        if form.is_valid():
            metric_id = form.cleaned_data['metric_id']
            name = form.cleaned_data['metric_name']
            attribute_id = form.cleaned_data['attributes']
            metric_data_id = form.cleaned_data['metrics_data']
            old_attribute_id = form.cleaned_data['old_attribute_id']
            thresholds = form.cleaned_data['metric_thresholds']

            metric_orm = Metric.objects.get(id=metric_id)
            metric_orm.name = name
            metric_orm.data = None
            metric_orm.thresholds = thresholds
            if metric_data_id:
                metric_data_orm = MetricData.objects.get(id=metric_data_id)
                metric_orm.data = metric_data_orm
            metric_orm.save()

            # Add the metric to the new attribute
            if attribute_id != old_attribute_id:
                attribute = Attribute.objects.get(id=attribute_id)
                attribute.metrics.add(metric_orm)
                attribute.save()
                attribute = Attribute.objects.get(name=old_attribute_id)
                attribute.metrics.remove(metric_orm)
                attribute.save()

            state = EditorState(metrics=[metric_id], form=form)
            return shortcuts.render(request, 'prosoul/editor.html',
                                    build_forms_context(state))
        else:
            # TODO: Show error
            print(form.errors)
            raise Http404


class AttributeView(LoginRequiredMixin, JustPostMixin, View):

    @staticmethod
    def add_attribute(request):
        error = None
        form = forms_editor.AttributeForm(request.POST)
        if form.is_valid():
            goal_id = form.cleaned_data['goals_state']
            parent_id = form.cleaned_data['parent_id']
            goal_orm = None

            attribute_name = form.cleaned_data['attribute_name']
            attribute_orm = Attribute(name=attribute_name)
            try:
                attribute_orm.save()

                if parent_id:
                    # If there is an attribute parent use it instead of goal
                    parent_orm = Attribute.objects.get(name=parent_id)
                    parent_orm.subattributes.add(attribute_orm)
                    parent_orm.save()
                elif goal_id:
                    goal_orm = Goal.objects.get(id=goal_id)
                    goal_orm.attributes.add(attribute_orm)
                    goal_orm.save()
            except IntegrityError:
                attribute_orm = Attribute.objects.get(name=attribute_name)
                error = "Attribute %s alredy exists" % (attribute_name)

            context = EditorState(attributes=[attribute_orm.id], form=form)
            send_context = build_forms_context(context)
            send_context.update({"errors": error})
            return shortcuts.render(request, 'prosoul/editor.html', send_context)
        else:
            # TODO: Show error
            raise Http404


    @staticmethod
    def select_attribute(request, context=None):
        error = None
        template = 'prosoul/editor.html'
        form = forms_editor.AttributesForm(request.POST)
        if form.is_valid():
            attr_id = form.cleaned_data['id']
            attributes = [attr_id] if attr_id else []
            old_attributes = form.cleaned_data['attributes_state']
            if old_attributes == attr_id:
                # Unselect the attribute and its metrics
                form.cleaned_data['attributes_state'] = None
                form.cleaned_data['metrics_state'] = None
                attributes = None
            state = EditorState(form=form, attributes=attributes)

            return shortcuts.render(request, template,
                                    build_forms_context(state))
        else:
            state = EditorState(form=form)
            error = form.errors

        if context:
            context.update(build_forms_context(state))
        else:
            context = build_forms_context(state)

        context.update({"errors": error})
        return shortcuts.render(request, template, context)


    @staticmethod
    def remove_attribute(request):
        error = None
        form = forms_editor.AttributeForm(request.POST)
        if form.is_valid():
            attribute_name = form.cleaned_data['attribute_name']
            current_id = form.cleaned_data['current_id']
            try:
                Attribute.objects.get(id=current_id).delete()
            except Attribute.DoesNotExist:
                error = "Can't remove %s. Attribute does not exists." % attribute_name
            send_context = build_forms_context(EditorState(form=form, attributes=[]))
            send_context.update({"errors": error})
            return shortcuts.render(request, 'prosoul/editor.html', send_context)
        else:
            # TODO: Show error
            print("attribute_goal", form.errors)
            raise Http404


    @staticmethod
    def update_attribute(request):
        form = forms_editor.AttributeForm(request.POST)

        if form.is_valid():
            name = form.cleaned_data['attribute_name']
            current_id = form.cleaned_data['current_id']

            attribute_orm = Attribute.objects.get(id=current_id)
            attribute_orm.name = name
            attribute_orm.save()

            state = EditorState(attributes=[current_id], form=form)
            return shortcuts.render(request, 'prosoul/editor.html',
                                    build_forms_context(state))
        else:
            # TODO: Show error
            print(form.errors)
            raise Http404


class GoalView(LoginRequiredMixin, JustPostMixin, View):

    @staticmethod
    def add_goal(request):
        error = None
        form = forms_editor.GoalForm(request.POST)
        if form.is_valid():
            qmodel_id = form.cleaned_data['qmodel_state']
            qmodel_orm = None
            goal_name = form.cleaned_data['goal_name']
            goal_orm = Goal(name=goal_name)
            try:
                goal_orm.save()
                if qmodel_id:
                    qmodel_orm = QualityModel.objects.get(id=qmodel_id)
                    qmodel_orm.goals.add(goal_orm)
                    qmodel_orm.save()
            except IntegrityError:
                error = "Goal %s alredy exists" % (goal_name)
                goal_orm = Goal.objects.get(name=goal_name)

            context = EditorState(goals=[goal_orm.id], form=form)
            send_context = build_forms_context(context)
            send_context.update({"errors": error})
            return shortcuts.render(request, 'prosoul/editor.html', send_context)
        else:
            # TODO: Show error
            raise Http404

    @staticmethod
    def remove_goal(request):
        error = None
        form = forms_editor.GoalForm(request.POST)
        if form.is_valid():
            goal_name = form.cleaned_data['goal_name']
            current_id = form.cleaned_data['current_id']
            try:
                Goal.objects.get(id=current_id).delete()
            except Goal.DoesNotExist:
                error = "Can't remove %s. Goal does not exists." % goal_name
            send_context = build_forms_context(EditorState(goals=[], form=form))
            send_context.update({"errors": error})
            return shortcuts.render(request, 'prosoul/editor.html', send_context)
        else:
            # TODO: Show error
            print("remove_goal", form.errors)
            raise Http404

    @staticmethod
    def select_goal(request, context=None):
        error = None
        template = 'prosoul/editor.html'
        form = forms_editor.GoalsForm(request.POST)
        if form.is_valid():
            old_goals = form.cleaned_data['goals_state']
            goal_id = form.cleaned_data['id']
            goals = [goal_id]
            if old_goals == goal_id:
                # Unselect the goal and its attributes and metrics
                form.cleaned_data['goals_state'] = None
                form.cleaned_data['attributes_state'] = None
                form.cleaned_data['metrics_state'] = None
                goals = None
            state = EditorState(goals=goals, form=form)
        else:
            state = EditorState(form=form)
            error = form.errors

        if context:
            context.update(build_forms_context(state))
        else:
            context = build_forms_context(state)

        context.update({"errors": error})
        return shortcuts.render(request, template, context)


    @staticmethod
    def update_goal(request):
        form = forms_editor.GoalForm(request.POST)

        if form.is_valid():
            goal_name = form.cleaned_data['goal_name']
            current_id = form.cleaned_data['current_id']

            goal_orm = Goal.objects.get(id=current_id)
            goal_orm.name = goal_name
            goal_orm.save()

            state = EditorState(goals=[current_id], form=form)
            return shortcuts.render(request, 'prosoul/editor.html',
                                    build_forms_context(state))
        else:
            # TODO: Show error
            print(form.errors)
            raise Http404
