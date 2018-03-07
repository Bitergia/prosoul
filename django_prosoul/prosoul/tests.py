import json

from django.test import TestCase

from .prosoul_import import compare_models, convert_to_grimoirelab, feed_models


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
        # TODO is failing now
        format_ = 'alambic'
        filepath = 'prosoul/data/alambic_quality_model.json'
        fmodel = open(filepath, "r")
        import_models_json = json.load(fmodel)
        fmodel.close()
        if format_ != "grimoirelab":
            import_models_json = convert_to_grimoirelab(format_, import_models_json)
        feed_models(import_models_json)
        compare_models(import_models_json, format_)

    def off_test_import_export_ossmeter(self):
        """ Test the import/export process for quality models in ossmeter format """
        # TODO is failing now
        format_ = 'ossmeter'
        filepath = 'prosoul/data/ossmeter_qm.json'
        fmodel = open(filepath, "r")
        import_models_json = json.load(fmodel)
        fmodel.close()
        if format_ != "grimoirelab":
            import_models_json = convert_to_grimoirelab(format_, import_models_json)
        feed_models(import_models_json)
        compare_models(import_models_json, format_)
