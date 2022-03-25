import requests
from collections.abc import Iterable
from shapely.geometry import Point, Polygon
import pyproj as proj
from shapely.ops import nearest_points
from shapely.ops import transform
import os


api_key = os.getenv('API_KEY')

# Google Geocoding API
headers = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/96.0.4664.110 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Sec-GPC': '1',
    'Referer': 'http://viewer.sces.net:88/',
    'Accept-Language': 'en-US,en;q=0.9',
    'If-None-Match': '"1d807e7b43a7e9c"',
    'If-Modified-Since': 'Wed, 12 Jan 2022 19:07:55 GMT'
}

# define geosystem for distance measurements
crs_wgs = proj.Proj(init='epsg:4326')
crs_bng = proj.Proj(init='epsg:27700')


outage_RecID_list = []
outage_name_list = []
outage_modified_time_list = []
outage_start_time_list = []


def get_outages_json():
    outage_url = 'http://viewer.sces.net:88/data/outages.json'
    response = requests.get(outage_url, headers=headers, verify=False)
    outages = response.json()
    return outages


def get_outage_polygons_json():
    outage_url = 'http://viewer.sces.net:88/data/outagePolygons.json'
    response_polygon = requests.get(outage_url, headers=headers, verify=False)
    polygon_outages = response_polygon.json()
    return polygon_outages


def get_outage_summary():
    summary_url = 'http://viewer.sces.net:88/data/outageSummary.json'
    response_summary = requests.get(summary_url, headers=headers, verify=False)
    summary_outages = response_summary.json()
    return summary_outages


def format_summary_outages():
    summary = get_outage_summary()
    customers_affected = summary['customersAffected']
    customers_out = summary['customersOutNow']
    customers_restored = summary['customersRestored']
    return customers_affected, customers_out, customers_restored


def format_single_outages(outages):
    outage_point_list = [{'lat': 35.8300523, 'lng': -83.63353359999999}]
    for outage in outages:
        outage_point_list.append(outage['outagePoint'])
    return outage_point_list


def format_polygon_outages(polygon_outages):
    outage_polygon_coord_list = []
    outage_polygon_RecID_list = []
    polygon_customers_out = []
    for outage in polygon_outages:
        outage_polygon_RecID_list.append(outage['outageRecId'])
        polygon_customers_out.append(outage['outNow'])
        if 'type' in outage['points']:
            outage_polygon_coord_list.append(outage['points']['coordinates'])

    return outage_polygon_coord_list, polygon_customers_out


def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def transform_polygon_coordinates(outage_polygon_coord_list):
    polygon_coords_gen = []
    for polygon in outage_polygon_coord_list:
        flat_list = flatten(polygon)
        polygon_coords_gen.append(flat_list)

    coords_flat_list = []
    for gen in polygon_coords_gen:
        coord_values = []
        for g in gen:
            coord_values.append(g)
        coords_flat_list.append(coord_values)

    polygon_coords_tuple_list = []

    for poly in coords_flat_list:
        coords_polygon_flat_list_reversed = []
        it = iter(poly)
        coords_polygon_flat_list = [*zip(it, it)]
        for tup in coords_polygon_flat_list:
            tuple_reversed = tup[::-1]
            coords_polygon_flat_list_reversed.append(tuple_reversed)
        polygon_coords_tuple_list.append(coords_polygon_flat_list_reversed)
    return polygon_coords_tuple_list


def transform_point_coordinates(outage_points_list):
    # points formatting
    points_tuple_list = []
    for point in outage_points_list:
        lat = point['lat']
        lng = point['lng']
        points_tuple_list.append((lat, lng))
    return points_tuple_list


def address_geolocator(address):
    address = address.replace(' ', '+')
    url = f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}'
    response = requests.get(url)
    geocode_result = response.json()
    geo_lat = geocode_result['results'][0]['geometry']['location']['lat']
    geo_lng = geocode_result['results'][0]['geometry']['location']['lng']
    address_point = (geo_lat, geo_lng)
    address_point = Point(address_point)
    return address_point


def create_polygon_list(polygon_coords_list):
    polygon_list = []
    for p in polygon_coords_list:
        if len(p) > 2:
            poly = Polygon(p)
            polygon_list.append(poly)
    return polygon_list


# check for coordinate points match
def match_outage_point(address, address_point, point_outages, polygon_outage_list, monitor_radius):
    point_outage_check = False
    result = None
    for point in point_outages:
        outage_point = Point(point)
        if monitor_radius:
            monitor_radius_unit = (int(monitor_radius) / 3.281) / 100000
            if address_point.distance(outage_point) < monitor_radius_unit:
                result = 'Your address has power outage!'
                point_outage_check = True
                break
            else:
                point_outage_check = False
                continue

        elif address_point.almost_equals(outage_point, decimal=1):
            result = 'Your address has power outage!'
            point_outage_check = True
            break
        else:
            point_outage_check = False
            continue

    if point_outage_check is False:
        for polygon in polygon_outage_list:
            if monitor_radius:
                monitor_radius_unit = (int(monitor_radius) / 3.281) / 100000
                closest_polygon_point = nearest_points(polygon, address_point)
                closest_polygon_point = transform(lambda x, y: (y, x), closest_polygon_point[0])
                if address_point.distance(closest_polygon_point) < monitor_radius_unit:
                    result = 'Your address has power outage!'
                    point_outage_check = True
                    break
                else:
                    point_outage_check = False
                    continue

            elif polygon.contains(address_point):
                result = 'Your address appears to have a power outage'
                point_outage_check = True
                break
            else:
                point_outage_check = False
                continue

    if point_outage_check is False:
        result = f'No apparent outages at {address}'
    return result, point_outage_check


def maps_api_outage_coordinates(poly):
    dict_list = []
    for index in poly:
        single_polygon_list = []
        for subindex in index:
            mydict = {'lat': subindex[0], 'lng': subindex[1]}
            single_polygon_list.append(mydict)
        dict_list.append(single_polygon_list)

    return dict_list


def display_all_outages():
    outages_json = get_outages_json()
    outage_polygons_json = get_outage_polygons_json()
    single_outage_points = format_single_outages(outages_json)
    polygon_outages = format_polygon_outages(outage_polygons_json)
    transformed_outage_points = transform_point_coordinates(single_outage_points)
    transformed_polygons = transform_polygon_coordinates(polygon_outages)
    return transformed_outage_points, transformed_polygons


def outages_main_func(address=None, address_point=None, maps=None, outage_points=None, monitor_radius=False):
    outages_json = get_outages_json()
    outage_polygons_json = get_outage_polygons_json()
    single_outage_points = format_single_outages(outages_json)
    polygon_outages_customers_out = format_polygon_outages(outage_polygons_json)
    polygon_outages = polygon_outages_customers_out[0]
    transformed_outage_points = transform_point_coordinates(single_outage_points)
    transformed_polygons = transform_polygon_coordinates(polygon_outages)
    generated_polygon_list = create_polygon_list(transformed_polygons)

    if maps:
        google_maps_display_polygons = maps_api_outage_coordinates(transformed_polygons)
        return google_maps_display_polygons, polygon_outages_customers_out[1]
    if outage_points:
        return single_outage_points
    if address_point:
        result = match_outage_point(address, address_point, transformed_outage_points, generated_polygon_list, monitor_radius)
    else:
        address_point = address_geolocator(address)
        result = match_outage_point(address, address_point, transformed_outage_points, generated_polygon_list, monitor_radius)
    return result


# example address for testing purposes
# random_address = '119 Forks of the River Pkwy, Sevierville, TN 37862'
# res = outages_main_func(address=random_address)

