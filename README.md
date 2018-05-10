[![Build Status](https://travis-ci.org/OpenPathView/OPV_importData.svg?branch=master)](https://travis-ci.org/OpenPathView/OPV_importData)

Iso files need git lfs installed to be fetch cf. [git lfs](https://git-lfs.github.com/)

# Rederbro - Import data utility

## Context
Rederbro is the name we gave to our backpack, this backpack takes spherical pictures using 6 cameras and is also equiped
with a GPS and compass.

Pictures are saved on the 6 cameras SD cards and GPS/compass (we will call them RederbroMeta) are saved in a CSV file.
Note that the cameras doesn't have their own batteries they are connected on a central battery that not always
plugged in, this mean they can loose their dates and time.

It's really long to manually copy all pictures from SD card and organize them. Also to make spherical pictures
we need to group the pictures and associate the correct RederbroMeta to a set of 6 images. Camera syncrhonization is
suppose to be good, but sometimes some cameras may fail (and not take all pictures). Date and times on the RederbroMeta
is also not always occurate (in absolute value) as the backpack isn't always on power supply.

What we have is relative timings on the camera pictures exif data and in the CSV file, we also know that most of the
time pictures and RederbroMeta are taken saved correctly. For that we made an algorithm to maximise the matches and 
generate set of 6 images matched with RederbroMeta. A set of 6 images with the RederbroMeta is called a Lot.

All generated Lot are then saved in database using our [API](https://github.com/OpenPathView/OPV_DBRest), pictures are
saved using our [DirectoryManager](https://github.com/OpenPathView/DirectoryManager) (more details about our 
infrastructure and containers deployment script are [here](https://github.com/OpenPathView/OPV_Ansible)).

## Installation

We use udiskctl to mount and umount devices :
```bash
apt install udisks2
```

### Install opv_import python module

You should use a virtualenv.

`python setup.py install` or, if you're developing on it, `python setup.py develop`

## Step to import data

### Batch copy images from all cards

You don't want to manipulate cards as it takes times, that's why we made a script that will listen on new plugged devices 
and copy DCIM folders from all configured camera SD cards, even if they are all plugged at the same time. For Open Path View, 
we use an USB3.0 hub to plug our 6 SD cards at the same time after the import script is launched.

```bash
opv-sd-copier -h  # for full details
opv-sd-copier /tmp/import_cameras_output
```

If you are using gnome, be sure to disable gnome auto-mount feature using this command :
```bash
gsettings set org.gnome.desktop.media-handling automount false
# to ensable it back
# gsettings set org.gnome.desktop.media-handling automount true
```

### Make lot

Now you have your images (and maybe a CSV file with RederbroMeta), you can launch the following command to make lots.
All lots will be associated to a campaign in the database, you can specify the name, description and id_rederbro of the 
campaign.

```bash
opv-make-lot -h # for full details
opv-make-lot /tmp/import_cameras_output --csv-path=picturesInfocsv --campaign-name="After refacto"
```

This commands may take some times, don't worry. *You might need to configure the APIs endpoints, see `opv-make-lot -h` to see the options.*

## Storage devices

Each camera has an SD card. To know who is who when importing we needed to know from which camera comes an SD card to 
do so we add a configuration file to the camera a file named `APN_config.json`.

#### Configure each SD card

We made an utility to do that, simply run `opv-sd-configurer` an insert your cards, you will be asked for each card
to enter it's `apn_number` (apn number must start at 0, for us it's from 0 to 5 as we have 6 cameras).

#### Clean SD card

After data are copied, we needed an easy and efficient way of cleaning the SD cards. We made a script that will burn an 
iso (disk image) on all plugged (and configured) devices. This disk image represent an SD card just after we format it 
in the camera. Camera sometimes add some data on the SD card after formating it that why we prefer tu burn a clean image 
(build by the camera) and we don't use FAT32 formating tool (see below how you can make the disk image).

When you have the image simply run (if you have 6 devices, script will stop after they are cleaned) :
```bash
opv-sd-cleaner iso/goPro.iso --number-of-devices=6
```

#### Make the clean disk image
SD cards for GoPro cameras needs to be well formated. The only way to do that is to format an SD card in a GoPro camera an copy it's partition table.
To do so :
- format your SD card in a GoPro camera
- Make an ISO : `sudo dd if=/dev/sdb of=imgGoPro.img bs=10M count=1`


# License

Copyright (C) 2018 Open Path View <br />
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
