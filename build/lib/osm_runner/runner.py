from arcgis.geometry import Point, Polyline, Polygon
from arcgis.features import GeoAccessor

from datetime import date
import pandas as pd
import requests


class Runner:

    def __init__(self):

        # OSM Element Types
        self.elements = {"point": "node", "line": "way", "polygon": "way"}

        # Period: http://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL
        # Section 5 / 5.1
        self.output = '(._;>;);out geom qt;'

        # Format: http://wiki.openstreetmap.org/wiki/Overpass_API/Language_Guide
        # Section 13 / 13.1
        self.format = '[out:json]'

    def gen_osm_df(self, geom_type, bound_box, osm_tag=None, time_one=None, time_two=None, present=False):

        geom_type = geom_type.lower()

        if geom_type not in self.elements.keys():
            raise Exception(f'Geometry Type "{geom_type}" Does Not Match Input Options: point|line|polygon')

        else:
            osm_element = self.elements.get(geom_type)

            query = self.get_query(osm_element, bound_box, osm_tag, time_one, time_two, present)

            osm_response = self.get_osm_elements(query)

            if geom_type == 'point':
                base_df = self.build_node_sdf(osm_response)

            else:
                base_df = self.build_ways_sdf(osm_response, geom_type)

            df = self.fields_cleaner(base_df)

            return df

    def get_query(self, osm_el, b_box, o_tag, t1, t2, present_flag):

        if osm_el.lower() not in self.elements.values():
            raise Exception(f'OSM Element {osm_el} Does Not Match Configuration Options: node|way')

        head = self.get_query_head(self.format, t1, t2, present_flag)

        if isinstance(o_tag, dict):

            o_tag, filters = next(iter(o_tag.items()))

            filters = [f.lower() for f in filters]
            f = '|'.join(filters)
            f_clause = '["' + o_tag + '"~"' + f + '"]'
            return ';'.join([head, ''.join([str(osm_el), f_clause, str(b_box)]), self.output])
            # E.G. [out:json];way["highway"~"primary|residential"](bounding_box);(._;>;);out geom qt;

        elif isinstance(o_tag, str):

            f_clause = '["' + o_tag + '"]'
            return ';'.join([head, ''.join([str(osm_el), f_clause, str(b_box)]), self.output])
            # E.G. [out:json];way["highway"](bounding_box);(._;>;);out geom qt;

        else:
            return ';'.join([head, ''.join([str(osm_el), str(b_box)]), self.output])
            # E.G. [out:json];way(bounding_box);(._;>;);out geom qt;

    @staticmethod
    def get_query_head(f, t_1, t_2, p_flag):

        if not t_1 and not t_2:
            return f

        else:
            if p_flag:
                if t_1 and not t_2:
                    d = '[diff: "' + t_1 + '", "' + date.today().strftime('%Y-%m-%d') + '"]'

                elif t_2 and not t_1:
                    d = '[diff: "' + t_2 + '", "' + date.today().strftime('%Y-%m-%d') + '"]'

                else:
                    raise Exception('Invalid Parameters - Please Only Specify One Time Parameter When Using Present')

            else:
                if t_1 and not t_2:
                    d = '[date: "' + t_1 + '"]'

                elif t_2 and not t_1:
                    d = '[date: "' + t_2 + '"]'

                else:
                    d = '[diff: "' + t_1 + '", "' + t_2 + '"]'

        return ''.join([f, d])

    @staticmethod
    def get_osm_elements(osm_query):

        osm_api = 'https://overpass-api.de/api/interpreter'

        r = requests.get(osm_api, data=osm_query)

        if r.status_code == 200:

            if len(r.json()['elements']) == 0:

                try:
                    raise Exception(f'OSM Returned Zero Results with Remark: {r.json()["remark"]}')

                except KeyError:
                    raise Exception(f'OSM Returned Zero Results for Query: {osm_query}')

            else:
                return r.json()['elements']

        elif r.status_code == 429:
            raise Exception('OSM Request Limit Reached. Please Try Again in a Few Minutes . . .')

        else:
            raise Exception(f'OSM Returned Status Code: {r.status_code}')

    @staticmethod
    def build_node_sdf(n_list):

        # List of Node Dictionaries for Data Frame Creation
        data_list = []

        for node in n_list:

            # Set Initial Values
            node_data = {
                'osm_id': str(node['id']),
                'geom': Point({
                    "x": node['lon'],
                    "y": node['lat'],
                    "spatialReference": {"wkid": 4326}
                })
            }

            # Push All Tag Values into Node Data
            for k, v in node['tags'].items():
                node_data.update({k: v})

            data_list.append(node_data)

        try:
            df = pd.DataFrame(data_list)
            df.spatial.set_geometry('geom')

            return df

        except Exception as e:
            raise Exception(f'Building Spatial Data Frame Failed: {e}')

    @staticmethod
    def build_ways_sdf(o_response, g_type):

        # Extract Relevant Way Elements from OSM Response
        if g_type == 'polygon':
            ways = [e for e in o_response if e['type'] == 'way' and e['nodes'][0] == e['nodes'][-1]]
        else:
            ways = [e for e in o_response if e['type'] == 'way' and e['nodes'][0] != e['nodes'][-1]]

        # List of Node Dictionaries for Data Frame Creation
        data_list = []

        for way in ways:
            try:

                # Collect Geometry
                coords = [[e['lon'], e['lat']] for e in way.get('geometry')]
                if g_type == 'polygon':
                    poly = Polygon({"rings":  [coords], "spatialReference": {"wkid": 4326}})
                else:
                    poly = Polyline({"paths": [coords], "spatialReference": {"wkid": 4326}})

                # Set Initial Values
                way_data = {
                    'osm_id': str(way['id']),
                    'geom': poly
                }

                # Push All Tag Values into Node Data
                for k, v in way['tags'].items():
                    way_data.update({k: v})

                data_list.append(way_data)

            except Exception as e:
                print(f'Way ID {way["id"]} Raised Exception: {e}')

        try:
            df = pd.DataFrame(data_list)
            df.spatial.set_geometry('geom')

            return df

        except Exception as e:
            raise Exception(f'Building Spatial Data Frame Failed: {e}')

    @staticmethod
    def fields_cleaner(b_df):

        # Set Cutoff & Collect Field List
        cutoff = int(len(b_df) * .99)
        f_list = list(b_df)

        # Flag Fields Where >= 99% of Data is Null
        fields = []
        for f in f_list:
            try:
                if b_df[f].dtype == 'object' and f != 'SHAPE':
                    null_count = b_df[f].value_counts().get('Null', 0)
                    if null_count >= cutoff:
                        fields.append(f)
            except:
                print(f'Cannot Determine Null Count for Field {str(f)}')
                continue

        # Drop Flagged Fields & Return
        if fields:
            b_df.drop(fields, axis=1, inplace=True)
            return b_df

        else:
            return b_df
