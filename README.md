# Prosoul [![Build Status](https://travis-ci.org/Bitergia/prosoul.svg?branch=master)](https://travis-ci.org/Bitergia/prosoul)

**Prosoul** is a software quality models manager to create, import/export, view and edit
models.


## Description

The goal of this project is to create a web editor and viewer for [software quality models](https://github.com/borisbaldassari/se-quality-models) that are used to show metrics in a meaning way. Also, importers and exporters for the different quality models used in the industry will be implemented so they can be used as models or evolved for the creation of new quality models.

In the initial version the metrics supported will be the [CROSSMINER ones](https://github.com/crossminer/crossminer/tree/dev/web-dashboards/ossmeter-metrics).

Based on the models, visualizations and assessment for the projects are generated. In the inital version
Kibana dashoards will be created using [GrimoireLab](http://grimoirelab.github.io/).

The final goal is to have a tool for "Automatic Project Assessment and Visualization based on Evolved Quality Models".

The original name for this project was Meditor but is was chaged to Prosoul because meditor already was used in pip.

## Source code and contributions

All the source code is available in the [Prosoul GitHub repository](https://github.com/Bitergia/prosoul). Please, upload pull requests if you have proposals to change the source code, and open an issue if you want to report a bug, ask for a new feature, or just comment something.

The [code of conduct](CODE_OF_CONDUCT.md) must be followed in all contributions
to the project.

## Execution

**Prosoul** is a Django application so to run it you need django installed.

```
prosoul/django_prosoul $ python3 manage.py makemigrations
prosoul/django_prosoul $ python3 manage.py migrate
prosoul/django_prosoul $ python3 manage.py runserver
```

By default the applicacion will be accesible in: http://127.0.0.1:8000/

A docker image is also available to execute the application:

```
prosoul/docker $ docker-compose up
```

## Basic Usage

There is two introductory videos: showing the import and view feature, and howto use the editor for adding a new quality model:

* Import and view of quality models: [prosoul-intro.webm](https://raw.githubusercontent.com/Bitergia/prosoul/master/doc/meditor-intro.webm)
* Adding a new quality model: [prosoul-editor.webm](https://raw.githubusercontent.com/Bitergia/prosoul/master/doc/meditor-editor.webm)
* Creating a viz and an assessment based on a quality model: [prosoul-viz-assess.webm](https://raw.githubusercontent.com/Bitergia/prosoul/master/doc/meditor-viz-assess.webm)

## Import / Export

Import and export for quality models can be done using the web interface or
from the command line:

* Import a model from a OSSMeter JSON file:

```
prosoul/django_prosoul $ PYTHONPATH=. prosoul/prosoul_import.py -f prosoul/data/ossmeter_qm.json --format ossmeter
```

* Export a model to a GrimoireLab JSON file:

```
prosoul/django_prosoul $ PYTHONPATH=. prosoul/prosoul_export.py -f prosoul/data/ossmeter_qm_grimoirelab.json --format grimoirelab -m "Default OSSMETER quality model"
```

## Requirements

* Python >=3.4
* setuptools
* django
* kidash
* requests

## Architecture

A draft diagram for the architecture is:

![](doc/prosoul-arch.png?raw=true)

## Prosoul in CROSSMINER

There is a specific guide for [using prosoul in CROSSMINER](doc/prosoul-crossminer.md) for creating the visualization for a quality model and generating the assessment of the projects in CROSSMINER.

There is a [demo online of prosoul for CROSSMINER](http://meditor.castalia.camp).


## License

Licensed under GNU General Public License (GPL), version 3 or later.
