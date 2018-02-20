# meditor

**meditor** is a software quality models manager to create, import/export, view and edit
models.


## Description

The goal of this project is to create a web editor and viewer for [software quality models](https://github.com/borisbaldassari/se-quality-models) that are used to show metrics in a meaning way. Also, importers and exporters for the different quality models used in the industry will be implemented so they can be used as models or evolved for the creation of new quality models.

In the initial version the metrics supported will be the [CROSSMINER ones](https://github.com/crossminer/crossminer/tree/dev/web-dashboards/ossmeter-metrics).

Based on the models, visualizations for metrics are generated. In the inital version
Kibana dashoards will be created using [GrimoireLab](http://grimoirelab.github.io/).

## Source code and contributions

All the source code is available in the [Meditor GitHub repository](https://github.com/Bitergia/meditor). Please, upload pull requests if you have proposals to change the source code, and open an issue if you want to report a bug, ask for a new feature, or just comment something.

The [code of conduct](CODE_OF_CONDUCT.md) must be followed in all contributions
to the project.

## Execution

**meditor** is a Django application so to run it you need django installed.

```
meditor/django_meditor $ python3 manage.py runserver
```

By default the applicacion will be accesible in: http://127.0.0.1:8000/

A docker image is also available to execute the application:

```
meditor/docker $ docker-compose up
```

## Basic Usage

There is two introductory videos: showing the import and view feature, and howto use the editor for adding a new quality model:

* Import and view of quality models: [meditor-intro.webm](https://raw.githubusercontent.com/Bitergia/meditor/master/meditor-intro.webm)
* Adding a new quality model: [meditor-editor.web](https://raw.githubusercontent.com/Bitergia/meditor/master/meditor-editor.webm)

## Import / Export

Import and export for quality models can be done using the web interface or
from the command line:

* Import a model from a OSSMeter JSON file:

```
meditor/django_meditor $ PYTHONPATH=. meditor/meditor_import.py -f meditor/data/ossmeter_qm.json --format ossmeter
```

* Export a model to a GrimoireLab JSON file:

```
meditor/django_meditor $ PYTHONPATH=. meditor/meditor_export.py -f meditor/data/ossmeter_qm_grimoirelab.json --format grimoirelab -m "Default OSSMETER quality model"
```

## Requirements

* Python >=3.4
* Django 2

## License

Licensed under GNU General Public License (GPL), version 3 or later.
