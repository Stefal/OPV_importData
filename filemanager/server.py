#!/usr/bin/python3
# coding: utf-8
"""Api server and db

Usage:
  server.py run [--db-location=<str>] --storage-location=<str> [--debug]
  server.py (-h | --help)

Options:
  -h --help                  Show this screen.
  --db-location=<path>       Set the database location (e.g sqlite:////tmp/test.db) [default: in-memory]
  --storage-location=<path> The path to the storage location
  --debug               Allow to stop the server on /shutdown
"""
import os.path

from docopt import docopt

from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_potion import Api, ModelResource
from flask_potion.fields import Inline

debug = False

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

storage_location = ''

def determine_path_from_uuid(uuid):
    return os.path.join(storage_location, str(uuid))


###
# Defining database
###

db = SQLAlchemy(app)

class File(db.Model):
    uuid = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(250))

###
# Defining all ressources
###

class FileRessource(ModelResource):
    class Meta:
        model = File
        excluded_fields = ['path']

    @ModelResource.instances.POST(rel='create')
    def create(self,):
        proterties = dict()
        f = self.manager.create(proterties)

        path = determine_path_from_uuid(f.uuid)

        # Ensure path really exists, make it otherwise
        if not os.path.exists(path):
            os.makedirs(path)

        proterties['path'] = path

        self.manager.update(f, proterties)
        return f
    create.request_schema = None  # Take no args
    create.response_schema = Inline('self')  # return a File like object


api = Api(app)
api.add_resource(FileRessource)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    if debug:
        shutdown_server()
        return 'Server shutting down...'
    return "You can't shut the server down"

def makeAndRun(db_location):
    if db_location and db_location != "in-memory":
        app.config['SQLALCHEMY_DATABASE_URI'] = db_location
    db.create_all()
    app.run(port=5001)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    debug = bool(arguments.get('--debug'))
    storage_location = arguments['--storage-location'] or ''
    makeAndRun(arguments['--db-location'])
