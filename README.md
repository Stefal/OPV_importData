[![Build Status](https://travis-ci.org/OpenPathView/OPV_importData.svg?branch=master)](https://travis-ci.org/OpenPathView/OPV_importData)

Iso files need git lfs installed to be fetch cf. [git lfs](https://git-lfs.github.com/).

# Requirements

## Git LFS
Before clonning this repository, you need to install **git-lfs**. You should follow [the git-lfs install guide](https://help.github.com/articles/installing-git-large-file-storage/).

## APIs
To import the datasets you need 2 webservice :
 - [OPV_DBRest](https://github.com/Openpathview/OPV_DBrest) : you will need to kown it's endpoint. This API will be used to store all metadata.
 - [DirectoryManager](https://github.com/OpenPathView/DirectoryManager) : you will also need to know it's endpoint. This API is our storage API.

## Host configuration
We will use **opv_master**, we have DB_Rest and the DirectoryManager on this machine. You might set it in your /etc/hosts file.

# Install

First clone this repository :
```bash
git clone https://github.com/OpenPathView/DirectoryManager.git
```

*We suggest that you use a python virtualenv on run all the following commands in this virtualenv.*

To install the import script you simply need to run :
```bash
cd DirectoryManager
# switch in your venv
python setup.py install
```

# Importing test dataset
First you need to download our test dataset (7Gio).
```bash
cd /tmp
curl -L -o brestStreetsDataSet.tar.gz -C - https://storage.openpathview.fr/testDataSets/2017/brestStreetsDataSet.tar.gz
tar xvzf brestStreetsDataSet.tar.gz
```

Run **opv-import** with the test dataset :
```bash
opv-import --data-dir=/tmp/brestStreetsDataSet/SD --no-import --csv-path=/tmp/brestStreetsDataSet/picturesInfo.csv --dir-manager-uri=http://opv_master:5005 --api-uri=http://opv_master:5000 15 campaignName
```

# Cleaning SD cards

TODO

# Create GoPro Empty ISO
SD cards for GoPro cameras needs to be well formated. The only way to do that is to format an SD card in a GoPro camera an copy it's partition table.
To do so :
- format your SD card in a GoPro camera
- Make an ISO : `sudo dd if=/dev/sdb of=imgGoPro.img bs=10M count=1`
- specify the path of this ISO in OPV_importData/importData/config/main.json
