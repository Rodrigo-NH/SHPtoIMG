import random, os
from subprocess import Popen, PIPE, STDOUT
import json
from gdalwrap import scanfiles, Setsource, Layergrid, Transformation, layerclip
from gdalwrap import getfeatgeom, splitrings, splitvertices, geomptcount

inputfolder = r'D:\shapes\temp' # Input folder to scan for shapefiles
mapname = 'TestMap' # The final, compiled map name
splitshape = [1, 1] # Split input shapefiles ([lines, columns]). Usefull for big areas/big vertice count shapefiles
                    # ([1, 1]) means no splitting

lineType = '0x0004' # Default line tytpe (if 'typeattr' field is not found in shapefile)
pointType = '0x4b00' # Default point type (if 'typeattr' field is not found in shapefile)
polygonType = '0x0028' # Default polygon type (if 'typeattr' field is not found in shapefile)
labelattr = 'Glabel' # Field to search for feature labels in shapefiles attribute table
zoomattr = 'zoomL' # Field to search for zoom range (all range if not specified)
typeattr = 'Ftype' # Field to search for type
verticesthreshold = 253 # Set threshold to split geometried based on number of vertices.
                        # Split geometries if splitvertices > 2.
keepshapes = False # Save intermediate shapefiles in outputdir

mapEngine = r'D:\MapEngine\MapTk\MapTk.exe' # cgpsmapper or MapTk executable
gmtPath = r'D:\MapEngine\gmt.exe' # Gmaptool executable http://www.gmaptool.eu/en/content/gmaptool

def main():
    outpath = os.path.join(inputfolder, 'output')
    if not os.path.isdir(outpath):
        os.mkdir(outpath)
    shapefiles = scanfiles(inputfolder, 'shp')

    for shape in shapefiles:
        procshape(shape)

    allmaps = scanfiles(outpath, 'mp')
    for map in allmaps:
        compilemap(map)

    allimg = scanfiles(outpath, 'img')
    joinmaps(allimg)

def procshape(path):
    basename = os.path.basename(path).split('.')[0]
    outpath = os.path.join(inputfolder, 'output')
    mpfiles = scanfiles(outpath, 'mp')
    maprocs = []
    proc = True
    for rg in mpfiles:
        if basename in rg:
            proc = False
            maprocs.append(rg)

    if proc:
        inshp = Setsource(path, Action='open r')
        inshp.getlayer(0)
        tempset = []
        grid = Layergrid(inshp.layer, splitshape[0], splitshape[1], Type='tilenumbers')
        gridcol = grid.getgrid()
        inlayer = inshp.layer
        proj = Transformation(inshp.srs, '4326')
        for t in range(0, len(gridcol)):
            tempshp = Setsource(basename + '_' + grid.gridindex[t], Action='memory')
            tempshp.createlayer('', '4326', Type=inshp.layertypestr)
            fields = inshp.getattrtable()
            tempshp.setattrtable(fields)
            clipfeatures = layerclip(inlayer, gridcol[t])
            for feature in clipfeatures:
                geom = getfeatgeom(feature)
                geomt = proj.transform(geom)
                geomt.Simplify(0.000003)
                feature.SetGeometry(geomt)
                tempshp.createfeature(feature)
            if tempshp.featurecount() > 0:
                tempset.append(tempshp)
                outpathfile = os.path.join(outpath,basename + '_' + grid.gridindex[t]+'.shp')
                if keepshapes:
                    tempshp.savefile(outpathfile)

        for isubnshp in tempset:
            desc = isubnshp.datasource.GetDescription() + '.mp'
            mappath = os.path.join(outpath, desc)
            maprocs.append(mappath)
            mapname = 'Name=' + desc + '\n'
            hd = header()
            MAPid = str(random.randrange(10000000, 99999999))
            hd[3] = 'ID=' + MAPid + '\n'
            hd[4] = mapname
            MP = open(mappath, 'w', encoding='latin2')
            for line in hd:
                MP.write(line)
            ft = []
            print("Splitting rings and vertices...")
            backshape = Setsource(isubnshp.datasource.GetDescription() + '_P', Action='memory')
            backshape.createlayer(isubnshp.datasource.GetDescription() + '_P', isubnshp.srs, Type=isubnshp.layertypestr)
            fl = isubnshp.getattrtable()
            backshape.setattrtable(fl)
            it = isubnshp.iterfeatures(Action='reset')
            for feature in it:
                featset = splitrings(feature)
                for eachf in featset:
                    featset3 = splitvertices(eachf, verticesthreshold)
                    for f in featset3:
                        ft.append(f)
                        backshape.createfeature(f)
            outpathfile = os.path.join(outpath, isubnshp.datasource.GetDescription() + '_S' + '.shp')
            if keepshapes:
                backshape.savefile(outpathfile)
            simplified = Setsource(isubnshp.datasource.GetDescription() + '_SS', Action='memory')
            simplified.createlayer(isubnshp.datasource.GetDescription() + '_SS', isubnshp.srs, Type=isubnshp.layertypestr)
            simplifiedpath = os.path.join(outpath, isubnshp.datasource.GetDescription() + '_SS' + '.shp')
            simplified.setattrtable(fl)
            print("Constructing MP file...")
            for feat in ft:
                geom = getfeatgeom(feat)
                proj.transform(geom)
                tr = geomptcount(geom)
                if tr > 10:
                    geom = geom.Simplify(0.000003)
                    feat.SetGeometry(geom)
                simplified.createfeature(feat)
                dd = geom.ExportToJson()
                jsondt = json.loads(dd)
                ftype = ftypes(jsondt['type'])[0]
                ftypef = ftypes(jsondt['type'])[1]
                customlabel = ';Label='
                customzoom = '\nEndLevel=5' + '\nData0='
                try:
                    customzoomf = feat.GetField(zoomattr)
                    if customzoomf:
                        if 'n' in customzoomf:
                            lv = customzoomf.split('n')[1]
                            customzoom = '\nEndLevel=' + lv + '\nData0='
                        else:
                            customzoom = '\nData' + customzoomf + '='
                except: pass
                try:
                    getftypef = feat.GetField(typeattr)
                    if getftypef:
                        ftypef = getftypef
                except: pass
                try:
                    getcustomlabel = "Label="+feat.GetField(labelattr)
                    if getcustomlabel:
                        customlabel = getcustomlabel
                except: pass

                coorddata = jsondt['coordinates']
                if ftype == '[POLYGON]':
                    coorddata = coorddata[0][:-1]
                if ftype == '[POI]':
                    coordinner = []
                    coordinner.append(coorddata)
                    coorddata = coordinner
                datapart = ftype + '\nType=' + ftypef + '\n' + customlabel + customzoom
                coordline = ''
                for each in coorddata:
                    x = str(each[0])
                    y = str(each[1])
                    coordline = coordline + '(' + y + ',' + x +'),'
                datapart = datapart + coordline[:-1] + '\n[END]\n\n'
                MP.write(datapart)
            MP.close()
            if keepshapes:
                simplified.savefile(simplifiedpath)


def compilemap(map):
    me = mapEngine.split('\\')[-1].split('.')[0].upper()
    if me == 'MAPTK':
        ci = ' '
    if me == 'CGPSMAPPER':
        ci = ' -o '

    command = mapEngine + ' ' + map + ci + map.replace('.mp','.img')
    print("Processing: " + map)
    mapper = Popen(command, stdout = PIPE, stderr = STDOUT, shell = True)
    for line in mapper.stdout:
        print(line.decode('ansi').strip('\n'))


def joinmaps(allmaps):
    cp = os.path.commonpath(allmaps)
    img = ' '.join(allmaps)
    mappath = os.path.join(cp, mapname + '.img')
    command = gmtPath + ' -j -m ' + '"' + mapname + '"' + ' -o ' + \
              mappath + ' ' + img
    mapper = os.popen(command).read().splitlines()
    print(mapper)

def header():
    hd = [
        '[IMG ID]\n',
        'CodePage=1252\n',
        'LblCoding=9\n',
        'ID=?',
        'Name=?\n',
        'Preprocess=F\n',
        'TreSize=700\n',
        'TreMargin=0.00000\n',
        'RgnLimit=127\n',
        'Transparent=S\n',
        'POIIndex=Y\n',
        'Levels=7\n',
        'Level0=24\n',
        'Level1=23\n',
        'Level2=22\n',
        'Level3=21\n',
        'Level4=20\n',
        'Level5=19\n',
        'Level6=18\n',
        'Zoom0=0\n',
        'Zoom1=1\n',
        'Zoom2=2\n',
        'Zoom3=3\n',
        'Zoom4=4\n',
        'Zoom5=5\n',
        'Zoom6=6\n',
        '[END-IMG ID]\n\n'
    ]
    return hd

def ftypes(type):
    typeo = []
    if type == 'LineString':
        typeo.append('[POLYLINE]')
        typeo.append(lineType)
    elif type == 'Polygon':
        typeo.append('[POLYGON]')
        typeo.append(polygonType)
    elif type == 'Point':
        typeo.append('[POI]')
        typeo.append(pointType)
    return typeo

if __name__ == "__main__":
        main()