"""Api server and db

Usage:
  server.py run [--db-location=<str>] [--storage-location=<str>]
  server.py (-h | --help)

Options:
  -h --help                  Show this screen.
  --db-location=<path>       Set the database location (e.g sqlite:////tmp/test.db) [default: in-memory]
  --storage-location=<path> The path to the storage location

"""
import os.path

from docopt import docopt

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_potion import Api, ModelResource
from flask_potion.fields import Inline

app = Flask(__name__)

storage_location = ''

def determine_path_from_uuid(uuid):
    return os.path.join(storage_location, str(uuid))


###
# Defining database
###

db = SQLAlchemy(app)

class File(db.Model):
    uuid = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String())

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

        proterties['path'] = determine_path_from_uuid(f.uuid)

        self.manager.update(f, proterties)
        return f
    create.request_schema = None  # Take no args
    create.response_schema = Inline('self')  # return a File like object


api = Api(app)
api.add_resource(FileRessource)

def makeAndRun(db_location):
    if db_location and db_location != "in-memory":
        app.config['SQLALCHEMY_DATABASE_URI'] = db_location
    db.create_all()
    app.run(port=5001)


if __name__ == '__main__':
    arguments = docopt(__doc__)
    storage_location = arguments['--storage-location'] or ''
    makeAndRun(arguments['--db-location'])
