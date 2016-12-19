#!/bin/sh
# full the serveur with data to test

#Based on httpie

http :5000/campaign name='test' id_rederbro:='1' 
http :5000/sensors alt:=0 lat:=0 lng:0 degrees:=0 minutes:=0
http :5000/lot pictures_path:=0 goprofailed:=0 takenDate:='{"$date": 5}' campaign:=1 sensors:=1
http :5000/cp nb_cp:=5 search_algo_version="" stichable:=true lot:=1
http :5000/panorama cp:=1
http :5000/tile fallback_path:=0 param_location:=0 extension='' resolution:=0 max_level:=0 cube_resolution:=0 panorama:=1 lot:=1
