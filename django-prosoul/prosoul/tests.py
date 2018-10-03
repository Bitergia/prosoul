import json

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.management.commands.createsuperuser import get_user_model

from django_prosoul.settings import DATABASES

from rest_framework.test import APITestCase

from .prosoul_import import compare_models, convert_to_grimoirelab, feed_models

from .models import Goal

USER = "admin"
PASSWD = "admin"


class ProsoulREST(APITestCase):

    @staticmethod
    def setUpClass():
        # Let's create the user for testing
        admin_db = list(DATABASES.keys())[0]

        db_manager = get_user_model()._default_manager.db_manager(admin_db)
        db_manager.create_superuser(username=USER, email='', password=PASSWD)

    @staticmethod
    def tearDownClass():
        pass

    def tearDown(self):
        # Remove all items after each test
        api_urls = ['prosoul:metric-list', 'prosoul:metricdata-list', 'prosoul:factoid-list',
                    'prosoul:attribute-list', 'prosoul:goal-list', 'prosoul:qualitymodel-list']

        response = self.client.login(username=USER, password=PASSWD)

        for api_url in api_urls:
            # Get the list of items and remove them
            url = reverse(api_url)
            response = self.client.get(url, format='json')
            for item in response.data:
                response = self.client.delete(url + str(item['id']) + "/")
                self.assertEqual(response.status_code, 204)

    def test_api_list(self):
        response = self.client.login(username=USER, password=PASSWD)

        url = reverse('prosoul:metric-list')
        response = self.client.get(url, format='json')
        # The list must be empty
        self.assertEqual(len(response.data), 0)

        new_metric = {"name": "m1"}
        self.client.post(url, format='json', data=new_metric)
        response = self.client.get(url, format='json')
        # The list must have 1 metric
        self.assertEqual(len(response.data), 1)

    def test_api_creation(self):
        new_metric = {"name": "m1"}
        url = reverse('prosoul:metric-list')

        # Test creation without auth
        self.client.logout()
        response = self.client.post(url, format='json', data=new_metric)
        self.assertEqual(response.status_code, 403)

        # Test creation with auth
        self.client.login(username=USER, password=PASSWD)
        response = self.client.post(url, format='json', data=new_metric)
        self.assertEqual(response.status_code, 201)

        response = self.client.get(url + "1/", format='json')
        self.assertEqual(response.status_code, 200)

        # Remove the metric so no state is created after the test
        response = self.client.delete(url + "1/", format='json')

    def test_api_deletion(self):
        new_metric = {"name": "m1"}
        url = reverse('prosoul:metric-list')
        # No auth, forbidden
        response = self.client.delete(url + "1/", format='json')
        self.assertEqual(response.status_code, 403)
        self.client.login(username=USER, password=PASSWD)
        # Not exists, not found
        response = self.client.delete(url + "1/", format='json')
        self.assertEqual(response.status_code, 404)
        # Deleted correctly, no content returned (204)
        self.client.post(url, format='json', data=new_metric)
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 1)

        response = self.client.delete(url + "1/", format='json')
        self.assertEqual(response.status_code, 204)

        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data), 0)

    def test_api_update(self):
        new_metric = {"name": "m1"}
        update_metric = {"name": "m1updated"}
        url = reverse('prosoul:metric-list')
        self.client.login(username=USER, password=PASSWD)
        response = self.client.post(url, format='json', data=new_metric)
        self.assertEqual(response.data['name'], "m1")
        metric_id = str(response.data['id'])
        response = self.client.put(url + metric_id + "/", format='json', data=update_metric)
        self.assertEqual(response.data['name'], "m1updated")

    def test_api_metricdata(self):
        self.client.login(username=USER, password=PASSWD)
        new_item = {"implementation": "", "params": ""}
        url = reverse('prosoul:metricdata-list')
        response = self.client.post(url, format='json', data=new_item)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['implementation'], "")

    def test_api_datasourcetype(self):
        self.client.login(username=USER, password=PASSWD)
        new_item = {"name": "git"}
        url = reverse('prosoul:datasourcetype-list')
        response = self.client.post(url, format='json', data=new_item)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], "git")

    def test_api_metric(self):
        self.client.login(username=USER, password=PASSWD)
        new_item = {"name": "metric_test"}
        url = reverse('prosoul:metric-list')
        response = self.client.post(url, format='json', data=new_item)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], "metric_test")

    def test_api_factoid(self):
        self.client.login(username=USER, password=PASSWD)
        new_item = {"name": "factoid_test"}
        url = reverse('prosoul:factoid-list')
        response = self.client.post(url, format='json', data=new_item)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], "factoid_test")

    def test_api_attribute(self):
        self.client.login(username=USER, password=PASSWD)
        new_item = {"name": "attribute"}
        url = reverse('prosoul:attribute-list')
        response = self.client.post(url, format='json', data=new_item)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], "attribute")

    def test_api_goal(self):
        self.client.login(username=USER, password=PASSWD)
        new_item = {"name": "goal"}
        url = reverse('prosoul:goal-list')
        response = self.client.post(url, format='json', data=new_item)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], "goal")

    def test_api_qualitymodel(self):
        self.client.login(username=USER, password=PASSWD)
        new_item = {"name": "qualitymodel", "goals": []}
        url = reverse('prosoul:qualitymodel-list')
        response = self.client.post(url, format='json', data=new_item)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], "qualitymodel")

    def test_nested_objects(self):
        self.client.login(username=USER, password=PASSWD)
        url = reverse('prosoul:qualitymodel-list')
        # The nested objects are defined by the name
        new_qualitymodel = {"name": "qualitymodel-nested", "goals": [{"name": "goal1"}, {"name": "goal2"}]}
        # The goals does not exists yet, so it must fail
        # TODO: Right now an exception in the server occurs and it is not sent to the client
        # TODO: so the client only knows that something went wrong
        try:
            response = self.client.post(url, format='json', data=new_qualitymodel)
        except Goal.DoesNotExist:
            # TODO: But the quality model is created ... we need to review this in the API REST implementation
            response = self.client.delete(url + "1/", format='json')
        goal1 = {"name": "goal1"}
        goal2 = {"name": "goal2"}
        url = reverse('prosoul:goal-list')
        response = self.client.post(url, format='json', data=goal1)
        self.assertEqual(response.status_code, 201)
        response = self.client.post(url, format='json', data=goal2)
        self.assertEqual(response.status_code, 201)
        url = reverse('prosoul:qualitymodel-list')
        response = self.client.post(url, format='json', data=new_qualitymodel)
        self.assertEqual(response.status_code, 201)


class ProsoulImportExport(TestCase):

    def test_import_export_grimoirelab(self):
        """ Test the import/export process for quality models in grimoirelab format """
        format_ = 'grimoirelab'
        filepath = 'prosoul/data/grimoirelab_ossmeter_qm.json'
        fmodel = open(filepath, "r")
        import_models_json = json.load(fmodel)
        fmodel.close()
        if format_ != "grimoirelab":
            import_models_json = convert_to_grimoirelab(format_, import_models_json)
        feed_models(import_models_json)
        compare_models(import_models_json, format_)

    def off_test_import_export_alambic(self):
        """ Test the import/export process for quality models in alambic format """
        # TODO is failing now because assertDictEqual and keys ordering
        format_ = 'alambic'
        filepath = 'prosoul/data/alambic_quality_model.json'
        fmodel = open(filepath, "r")
        import_models_json = json.load(fmodel)
        fmodel.close()
        models = import_models_json
        if format_ != "grimoirelab":
            models = convert_to_grimoirelab(format_, import_models_json)
        feed_models(models)
        compare_models(import_models_json, format_)

    def off_test_import_export_ossmeter(self):
        """ Test the import/export process for quality models in ossmeter format """
        # TODO is failing now because assertDictEqual and keys ordering
        format_ = 'ossmeter'
        filepath = 'prosoul/data/ossmeter_qm.json'
        fmodel = open(filepath, "r")
        import_models_json = json.load(fmodel)
        fmodel.close()
        models = import_models_json
        if format_ != "grimoirelab":
            models = convert_to_grimoirelab(format_, import_models_json)
        feed_models(models)
        compare_models(import_models_json, format_)
