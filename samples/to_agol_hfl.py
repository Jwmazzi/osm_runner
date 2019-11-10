from arcgis.features import GeoAccessor
from arcgis.gis import GIS
import pandas as pd
import time

from osm_runner import Runner


if __name__ == "__main__":

    # Load Extent from Local Shapefile
    sdf = GeoAccessor.from_featureclass('..\\data\\DC\\DC.shp')
    ext = sdf.iloc[0]['SHAPE'].extent

    # Format Extent for Overpass API (S, W, N, E)
    bbox = f'({ext[1]},{ext[0]},{ext[3]},{ext[2]})'

    # Get Instance of OSM Runner
    runner = Runner()

    # # Fetch Surveillance Cameras
    # df = runner.gen_osm_df('point', bbox, 'man_made')

    # Fetch Surveillance Cameras
    df = runner.gen_osm_df('point', bbox, 'man_made')

    # # Fetch Historic Buildings
    # df = runner.gen_osm_df('line', bbox, 'historic')

    gis = GIS('https://dbsne.maps.arcgis.com', 'jscarmazzi_DBSNE', 'gis12345')

    df.spatial.to_featurelayer(f'OSM Cameras {round(time.time())}', gis=gis)


