[![Build Status](https://travis-ci.org/naegi/batchPanoMaker.svg?branch=master)](https://travis-ci.org/naegi/batchPanoMaker)

# Batch Pano Maker
Scripts that import data from our backpack, make data sets with metas (GPS, orientation ....) and stitch all panoramas.

/!\ Need Hugin for CP_stats.py

## Installation
### Start by creating a venv
`virtualenv mon_env -p /usr/bin/python3.4 --no-site-packages`
### Go inside
`. mon_env/bin/activate`
### Install all dependencies
`pip install -r requirements.txt`
### Install importData
`./setup.py install` or, if you're developing on it, `./setup.py develop`

## Launch
### First the filemanger server
`python filemanager/server.py run --storage-location=/home/tom/Documents/OPV/batchPanoMaker/temp`
### Then the api server
`python api/server.py run`
### Then launch the import from importData dir
`opv-import capucin --csv-path=/home/tom/Documents/OPV/batchPanoMaker/importData/picturesInfo.csv`

## Architecture
This software is now composed of three components:
 * A filemanager server - a simple server that allow to make a link between unique ID and directory, will quickly be remplaced by [a more complete solution](https://github.com/OpenPathView/DirectoryManager/). See into filemanager.
 * An API server - a simple REST server that expose a DB. See into api/.
 * The import data script - a script that import data from sd-cards, make lots and exports all data into the DB through the api and the filemanager.

### Filemanager
The server is listening on port 5001.
#### Usage
I use [httpie](https://httpie.org/) here.
Get an ID and a path:
`http POST :5001/file`
Returns:
```json
{
   "$uri": "/file/1",
   "path": "/tmp/1"
}
```
Get the path from the ID (by exemple ID=1):
`http GET :5001/file/1`
Returns:
```json
{
    "$uri": "/file/1",
    "path": "/tmp/1"
}
```
Some content for more easy debugging:
- stop the server (only if --debug is precised while launching the server): `http POST :5000/shutdown`

### API
It's a server located on port 5000
The API server implement this database:
![Database](https://raw.githubusercontent.com/OpenPathView/batchPanoMaker/master/doc/database/main_db.png)
And some content for more easy debugging:
- get all lots of an campaign (here campaign ID=1): `httpie GET :5000/campaign/1/lots`
- get all cp of a lot (here lot ID=1): `httpie GET :5000/lot/1/cps`
- get all tiles of a panorama (here panorama ID=1): `httpie GET :5000/panorama/1/tiles`
- stop the server (only if --debug is precised while launching the server): `http POST :5000/shutdown`


### Import data script
This script imports, detect sd-card, mount them using udisks2 (udiskctl), copy all images to data dir and create lots.
See `import.py --help` for options.
There are also statics options in batchPanoMaker/importData/config/main.json
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
- specify the path of this ISO in batchPanoMaker/importData/config/main.json
