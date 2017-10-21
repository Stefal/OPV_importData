[![Build Status](https://travis-ci.org/OpenPathView/OPV_importData.svg?branch=master)](https://travis-ci.org/OpenPathView/OPV_importData)

Iso files need git lfs installed to be fetch cf. [git lfs](https://git-lfs.github.com/)

# Batch Pano Maker
Scripts that import data from our backpack, make data sets with metas (GPS, orientation ....) and stitch all panoramas.

/!\ Need Hugin for CP_stats.py

## Installation
apt install udisks2
### Start by creating a venv
`virtualenv mon_env -p /usr/bin/python3.5 --no-site-packages`
### Go inside
`. mon_env/bin/activate`
### Install all dependencies
`pip install -r requirements.txt`
### Install importData
`./setup.py install` or, if you're developing on it, `./setup.py develop`

## Launch
### Then the api server
`python api/server.py run`
### Then launch the import from importData dir
`opv-import capucin --csv-path=/home/tom/Documents/OPV/OPV_importData/importData/picturesInfo.csv`

## Architecture
This software is now composed of three components:
 * A filemanager server - a simple server that allow to make a link between unique ID and directory, will quickly be remplaced by [a more complete solution](https://github.com/OpenPathView/DirectoryManager/). See into filemanager.
 * An API server - a simple REST server that expose a DB. See into api/.
 * The import data script - a script that import data from sd-cards, make lots and exports all data into the DB through the api and the filemanager.

### API
It's a server located on port 5000
The API server implement this database:
![Database](https://raw.githubusercontent.com/OpenPathView/OPV_importData/master/doc/database/main_db.png)
And some content for more easy debugging:
- get all lots of an campaign (here campaign ID=1): `httpie GET :5000/campaign/1/lots`
- get all cp of a lot (here lot ID=1): `httpie GET :5000/lot/1/cps`
- get all tiles of a panorama (here panorama ID=1): `httpie GET :5000/panorama/1/tiles`
- stop the server (only if --debug is precised while launching the server): `http POST :5000/shutdown`


### Import data script
This script imports, detect sd-card, mount them using udisks2 (udiskctl), copy all images to data dir and create lots.
See `import.py --help` for options.
There are also statics options in OPV_importData/importData/config/main.json
- data-dir - default: ~/opv/rederbro/{campaign}/ - Where images from sd-cards are copied to.
- pi-location - default : pi@192.168.42.1:/home/pi/opv/lastPictureInfo.csv" - Where pictureInfo (metas from rederbro backpack) should be grabbed.
- ISO - default: ~/opv/iso/goPro.iso" - Where is the iso of an empty sd-card. Unutilized when clean-sd is false.
- clean-sd - default: false - Remove files from the sd-card (do a dd). Commented for the moment.
- import - default: true - Import files from sd-card
- export - default: true - Send lots into the celery queue
- treat - default: true - Make lots from data
- id-rederbro - default: 1 - The id of the rederbro
- lots-output-dir - default: ~/opv/lots/{campaign} - Where lots should be stored.

#### Make Empty ISO
SD cards for GoPro cameras needs to be well formated. The only way to do that is to format an SD card in a GoPro camera an copy it's partition table.
To do so :
- format your SD card in a GoPro camera
- Make an ISO : `sudo dd if=/dev/sdb of=imgGoPro.img bs=10M count=1`
- specify the path of this ISO in OPV_importData/importData/config/main.json


# License

Copyright (C) 2017 Open Path View <br />
This program is free software; you can redistribute it and/or modify  <br />
it under the terms of the GNU General Public License as published by  <br />
the Free Software Foundation; either version 3 of the License, or  <br />
(at your option) any later version.  <br />
This program is distributed in the hope that it will be useful,  <br />
but WITHOUT ANY WARRANTY; without even the implied warranty of  <br />
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the  <br />
GNU General Public License for more details.  <br />
You should have received a copy of the GNU General Public License along  <br />
with this program. If not, see <http://www.gnu.org/licenses/>.  <br />
