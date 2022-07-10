# ESRI shapefile to IMG for Garmin GPS

This script will convert ESRI shapefiles to IMG format Garmin maps. Uses external map processors (cgsmapper or MapTk).
## Requisites
- You will need Gdal python bindings installed. [Recipe](https://gist.github.com/Rodrigo-NH/7b9cbb9ea45edc13fc3f6606417d10ee) to get gdal and gdal bindings parts installed and configured in Windows  
- Map processors are Windows programs so this script must be used in Windows
- Uses gdalwrap package:  
		'pip install --user gdalwrap'  
		or https://github.com/Rodrigo-NH/gdalwrap
## Usage
The input folder for shapefiles to be used and other settings are in the script itself. Edit these variables in script and run.
- It will scan input folder, process all shapefiles and combine output to a single .img garmin map  

Optionally script will perform splitting of input shapefiles (Usefull for big areas/big vertice count shapefiles). Also optionally will split geometries by vertices count threshold. Script will remove rings, but keeping general geometries aspect, by splitting geometries containing rings into separate geometries. This is necessary as garmin (or map processor for instance) doesn't know about rings. 


## Labelling and styling
If not specified, vectors will use the styles defined in script's 'lineType', 'pointType' and 'polygonType' variables. Styling and labelling can be imported from shapefile attributes table. For this, edit the corresponding variables poiting to correct attribute names contained in the shapefile.

## Zoom levels
At the present moment script creates a fixed set of zoom levels (from 24 to 18), you can tweak that manually if you want. 
- If not specified, each feature will be tagged to show in all levels.
- It will import zoom level for each feature from attribute field 'zoomL' (Text field) following the rules: If it's a plain number (e.g. "4") it will tag the particular feature to show only on that level. If it's prefixed with the letter "n" (e.g. "n4") it will tag the feature for all levels until defined level (from 0 to 4 in this example)
## MP files
Script will not overwrite existing matching '.mp' files already present in the output directory. You need to delete them manually if you want to reconstruct the MP files. This can be usefull as script will compile the IMG files without overwriting corresponding MP file. For example if you need to make adjustments to MP files you can simply run the script again after changing the files.
## Map processors support
Support for available free map processors isn't great, unfortunately. There's basically two options: cgsmapper and MapTK. cgsmapper is not maintained and the official page doesn't exist anymore, it's possible to download the last version though from the internet. MapTk looks great, does a good job and software is active (last version from 2021), can be downloaded from http://www.maptk.de/ 

Cgsmapper page I tested and used to get cgsmapper: https://www.gpsfiledepot.com/tools/cgpsmapper.php
