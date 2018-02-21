from distutils.core import setup
setup(
  name = 'osm_runner',
  packages = ['osm_runner'], 
  version = '0.0.1',
  description = 'A simple ORM that leverages the SpatialDataFrames of the ArcGIS API for Python to integrate OSM data to the ArcGIS platform.',
  author = 'Jeffrey Scarmazzi',
  author_email = 'jscarmazzi@esri.com',
  url = 'https://github.com/Jwmazzi/osm_runner',
  download_url = 'https://github.com/jwmwzzi/osm_runner/archive/0.0.1.tar.gz', # I'll explain this in a second
  keywords = ['ArcGIS API for Python', 'OpenStreetMap'],
  classifiers = [],
)