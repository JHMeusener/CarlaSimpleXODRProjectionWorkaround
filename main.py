#!/usr/bin/env python

# Copyright (c) 2021 Jan-Hendrik Meusener
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# This Script is intended to modify a osm file such that the Simple-Projection of Carlas current (Version 0.9.11 and earlier) OSM to XODR Converter is negated
# and replaced by something like this: +proj=tmerc +lat_0=*middle latidude of streetnodes* +lon_0=*middle longitude of streetnodes* +x_0=0 +y_0=0 +ellps=GRS80 +units=m
# You can then simply drag the xodr-file into roadrunner etc and it matches with the osm files.
# Workflow:
# Run this script on the map.osm. This script creates a map_modified_for_Carla.osm and a replace_XodrHeader_with_this.txt.
# Run Carlas OSM to XODR Converter with SIMPLE projection (default) on the osm
# Replace the header in the resulting .xodr with the text in replace_XodrHeader_with_this.txt
# now the xodr should have a correct Projection and georeference for further use

import numpy as np
from pyproj import CRS, Transformer
import xml.etree.ElementTree as ET

osmPath = 'map.osm'
regionSpecificScaleFactor = 1.0



tree = ET.parse(osmPath)
root = tree.getroot()

global referenceLat
global referenceLon
referenceLat = None
referenceLon = None
minlat = 99999999.0
maxlat = -99999999.0
minlon = 99999999.0
maxlon = -99999999.0

#parse the osm-street nodes to get the "Middle" because Carla always centers on it
Streetnodelist = []
for entity in root:
    if entity.tag == "way":
        containsImportantNodes = False
        possibleNodes = []
        for entity_2 in entity:
            if 'k' in entity_2.attrib:
                if entity_2.attrib['k'] in ["highway"]:
                    if entity_2.attrib['v'] in ["unclassified", "secondary", "primary", "tertiary", "residential"]:
                        containsImportantNodes = True
            if 'ref' in entity_2.attrib:
                possibleNodes.append(entity_2.attrib['ref'])
        if containsImportantNodes:
            for nd in possibleNodes:
                Streetnodelist.append(int(nd))


for entity in root:
    if entity.tag == "node":
        if int(entity.attrib["id"]) in Streetnodelist:
            if minlat > float(entity.attrib["lat"]):
                    minlat = float(entity.attrib["lat"])
            if maxlat < float(entity.attrib["lat"]):
                    maxlat = float(entity.attrib["lat"])
            if minlon > float(entity.attrib["lon"]):
                    minlon = float(entity.attrib["lon"])
            if maxlon < float(entity.attrib["lon"]):
                    maxlon = float(entity.attrib["lon"])

middleLat = (maxlat+minlat)/2
middleLon = (maxlon+minlon)/2

crs_4326  = CRS.from_epsg(4326) # epsg 4326 is wgs84
uproj = CRS.from_proj4("+proj=tmerc +lat_0={0} +lon_0={1} +x_0=0 +y_0=0 +k_0={2} +ellps=GRS80 +units=m".format(middleLat,middleLon, regionSpecificScaleFactor))
transformer = Transformer.from_crs(crs_4326, uproj)

def preemtivelyReverseCarlasSIMPLEProjection(lat,lon, transformer):
    realX,realY = next(transformer.itransform([(lat,lon)]))
    #from carlas simple projection:
    #wrong_X = lon * 111320. * np.cos(lat*2.0*np.pi/360.)
    #wrong_Y = lat * 111136.
    fakeLat = realY / 111136.
    fakeLon = realX / (111320. * np.cos(fakeLat*2.0*np.pi/360.))
    return fakeLon,fakeLat

north,east = next(transformer.itransform([(maxlat,maxlon)]))
south,west = next(transformer.itransform([(minlat,minlon)]))

newOSMLocation = "/".join(osmPath.split("/")[:-1]+["map_modified_for_Carla.osm"])
for entity in root:
    if entity.tag == "node":
        x,y = preemtivelyReverseCarlasSIMPLEProjection(float(entity.attrib["lat"]),float(entity.attrib["lon"]), transformer)
        entity.attrib["lat"] = str(y)
        entity.attrib["lon"] = str(x)
with open(newOSMLocation, 'w') as f:
    tree.write(f, encoding='unicode')

#recheck the middle and add a offset to every node, because carla centers on the fake middle instead of the real reference one
tree = ET.parse(newOSMLocation)
root = tree.getroot()
minlat = 99999999.0
maxlat = -99999999.0
minlon = 99999999.0
maxlon = -99999999.0
for entity in root:
    if entity.tag == "node":
        if int(entity.attrib["id"]) in Streetnodelist:
            if minlat > float(entity.attrib["lat"]):
                    minlat = float(entity.attrib["lat"])
            if maxlat < float(entity.attrib["lat"]):
                    maxlat = float(entity.attrib["lat"])
            if minlon > float(entity.attrib["lon"]):
                    minlon = float(entity.attrib["lon"])
            if maxlon < float(entity.attrib["lon"]):
                    maxlon = float(entity.attrib["lon"])
middleLat_fake_offset = (minlat)
middleLon_fake_offset = (minlon)
wrongX_offset = middleLon_fake_offset * 111320. * np.cos(middleLat_fake_offset*2.0*np.pi/360.)
wrongY_offset = middleLat_fake_offset * 111136.
invtransformer = Transformer.from_crs(uproj,crs_4326)
latitude_correction,longitude_correction = next(invtransformer.itransform([(wrongX_offset,wrongY_offset)]))
if latitude_correction > 180 or longitude_correction > 180:
    latitude_correction = middleLat
    longitude_correction = middleLon

stringToPutAsODriveHeader = """<header revMajor="1" revMinor="4" name="" version="1" date="2019-02-18T13:36:12" north="{0}" south="{1}" east="{2}" west="{3}">
    <geoReference><![CDATA[+proj=tmerc +lat_0={4} +lon_0={5} +x_0=0 +y_0=0 +k_0={6} +ellps=GRS80 +units=m +no_defs]]></geoReference>
    </header>""".format(north,east,abs(south),abs(west),latitude_correction, longitude_correction, regionSpecificScaleFactor)

with open("/".join(osmPath.split("/")[:-1]+["replace_XodrHeader_with_this.txt"]), 'w') as f:
    f.write(stringToPutAsODriveHeader)
