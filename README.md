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

## Launch
### First the filemanger server
`python3.5 filemanager/server.py run --storage-location=/home/tom/Documents/OPv/batchPanoMaker/temp`
### Then the api server
`python3.5 api/server.py run`
### Then launch the import from importData dir
`python3.5 import.py capucin --csv-path=/home/tom/Documents/OPV/batchPanoMaker/importData/picturesInfo.csv`
