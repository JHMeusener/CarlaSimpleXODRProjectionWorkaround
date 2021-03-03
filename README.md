This Script is intended to modify a osm file such that the Simple-Projection of Carlas current (Version 0.9.11 and earlier) OSM to XODR Converter is negated
 and replaced by something like this: 
 "+proj=tmerc +lat_0=*middle latidude of streetnodes* +lon_0=*middle longitude of streetnodes* +x_0=0 +y_0=0 +ellps=GRS80 +units=m" 
 (Its the proj4 string)
 You can then simply drag the xodr-file into roadrunner etc and it matches with the osm files.


Workflow:
Run this script on the map.osm. This script creates a map_modified_for_Carla.osm and a replace_XodrHeader_with_this.txt.
Run Carlas OSM to XODR Converter with SIMPLE projection (default) on the osm
Replace the header in the resulting .xodr with the text in replace_XodrHeader_with_this.txt
now the xodr should have a correct Projection and georeference for further use

This Code works well for maps in the Europe. For other regions the projection string in this script may have to be adjusted. Some regions may not work at all.


This code was created as a part of
<p align="center"><img src="https://github.com/JHMeusener/osm2xodr/blob/master/Projekt%20und%20F%C3%B6rderlogos%20EN_28.11.2019.jpg" /></p>
