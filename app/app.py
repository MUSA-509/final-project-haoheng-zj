"""Musa 509 final project app"""
from flask import Flask, Response, render_template, escape, request, url_for
import json
import logging
import requests
import pandas as pd
from sqlalchemy import create_engine, String, Integer
from sqlalchemy.sql import text, bindparam
from google.cloud import bigquery
import geopandas as gpd
from shapely.geometry import shape
from datetime import datetime

try:
    from geopy import distance
except ImportError:
    pass

app = Flask(__name__, template_folder="templates")

# default origin
PHL_CITY_HALL_LAT = 39.95167975 
PHL_CITY_HALL_LNG = -75.1648285
MEYERSON_LAT = 39.9522197
MEYERSON_LNG = -75.1927961

# load credentials from a file
with open("./secrets/pg-credentials.json", "r") as f_in:
    pg_creds = json.load(f_in)

# mapbox credentials
with open("./secrets/mapbox_token.json", "r") as mb_token:
    MAPBOX_TOKEN = json.load(mb_token)["token"]

# # load bigquery credentials
# bqclient = bigquery.Client.from_service_account_json("./secrets/MUSA-509-3337814ad805.json")

app = Flask(__name__, template_folder="templates")

# load credentials from JSON file
HOST = pg_creds["HOST"]
USERNAME = pg_creds["USERNAME"]
PASSWORD = pg_creds["PASSWORD"]
DATABASE = pg_creds["DATABASE"]
PORT = pg_creds["PORT"]





def get_sql_engine():
    """Generates a SQLAlchemy engine"""
    return create_engine(f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}")

engine = get_sql_engine()


@app.route("/")
def index():
    """User input page"""
    return Response(render_template("index.html"), 200, mimetype="text/html")

# @app.route("/covid_viewer")
# def covid_viewer():

# def 

@app.route("/dest_info")
def dest_info():
    """Landing page"""
    address = get_address(request.args)
    error_message = None

    if address is not None:
        geocoded = geocoding(address).json()
        lng, lat = geocoded["features"][0]["geometry"]["coordinates"]

        # check if the geocoding results contain 'features'
        if "features" in geocoded:
            lng, lat = geocoded["features"][0]["geometry"]["coordinates"]
        else:
            error_message = (
                f"Invalid address entered ({address}). Here's Meyerson Hall. Please take a look at it."
            )
            lat, lng = MEYERSON_LAT, MEYERSON_LNG
            address = "Meyerson Hall, University of Pennsylvania"
    else:
        error_message = "No address entered! Here we set Meyerson Hall as your default destination. Please enter an address in Philadelphia or choose one from the drop-down list."
        lat, lng = MEYERSON_LAT, MEYERSON_LNG
        address = "Meyerson Hall, University of Pennsylvania"

    curr_time = get_current_time()

    zip_covid = get_zip_covid(lng, lat, error_message)
    num_pos_per, zip_code = zip_covid[0], zip_covid[1]
    error_message = zip_covid[2]

    test_sites = get_nearby_test_sites(lng, lat)
   
    dir_result = get_direction(PHL_CITY_HALL_LNG, PHL_CITY_HALL_LAT, lng, lat)
    geojson_str = dir_result[0]
    listToStr = dir_result[1]
    dir_data = dir_result[2] 
    dir_duration = dir_result[3]

    html_map = render_template(
        "destination_info.html",
        mapbox_token=MAPBOX_TOKEN,
        curr_time=curr_time,num_pos_per=num_pos_per,zip_code=zip_code,
        test_sites_1=test_sites[0], test_sites_2=test_sites[1], test_sites_3=test_sites[2],
        error_message=error_message,
        address=address,
        distance_from_ori=distance_from(lng, lat),
        lat=round(lat, 6),
        lng=round(lng, 6),
        ori_lat=PHL_CITY_HALL_LAT,
        ori_lng=PHL_CITY_HALL_LNG,

        html_map=render_template(
            "point_map.html", 
            dest_lat=lat, dest_lng=lng,
            ori_lat=PHL_CITY_HALL_LAT, ori_lng=PHL_CITY_HALL_LNG, 
            geojson_str=geojson_str, instr=listToStr, dir_data=dir_data, dir_duration=dir_duration,
            address=address,
            test_sites_1=test_sites[0], test_sites_2=test_sites[1], test_sites_3=test_sites[2],
            mapbox_token=MAPBOX_TOKEN)
    )
    logging.warning(html_map)

    html_response = f"""
    <div style='float:left;'>
    </div>
        {html_map}
        """
    response = Response(response=html_response, status=200, mimetype="text/html")
    return response


def get_address(args):
    """Parses query strings"""
    text_address = args.get("address_text")
    dropdown_address = args.get("address_dropdown")
    if text_address == "" and dropdown_address != "":
        return dropdown_address
    if text_address != "":
        return text_address
    return False


def geocoding(address):
    geocoding_call = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
        )
    resp = requests.get(geocoding_call, params={"access_token": MAPBOX_TOKEN})
    return resp


def distance_from(lng, lat):
    """Calculates the distance from Philadelphia City Hall"""
    return round(distance.distance((PHL_CITY_HALL_LAT, PHL_CITY_HALL_LNG), (lat, lng)).km, 2)


def get_current_time():
    curr_time = datetime.now().strftime("%B %d, %Y %I:%M %p")
    return curr_time


def get_direction(ori_lng, ori_lat, dest_lng, dest_lat):
    directions_resp = requests.get(
        f"https://api.mapbox.com/directions/v5/mapbox/driving/{ori_lng},{ori_lat};{dest_lng},{dest_lat}",
        params={
            "access_token": MAPBOX_TOKEN,
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "false",
        },
    )

    dir_duration = directions_resp.json()["routes"][0]['duration']
    dir_data = pd.DataFrame(
        directions_resp.json()["routes"][0]["legs"])

    dir_data = dir_data.iloc[:1].to_json()

    instruction=[]
    for step in directions_resp.json()['routes'][0]['legs'][0]['steps']:
        instruction.append(f"{step['maneuver']['instruction']}")
    listToStr = '<br>'.join(map(str, instruction))

    routes = gpd.GeoDataFrame(
        geometry=[
            shape(directions_resp.json()["routes"][idx]["geometry"])
            for idx in range(len(directions_resp.json()["routes"]))
        ]
    )   

    geojson_str = routes.iloc[:1].to_json()

    return geojson_str, listToStr, dir_data, dir_duration


def get_zip_covid(lng, lat, error_message):
    """Get Covid Test Results for Destination Zip Code"""
    zip_query = text(
        """
        SELECT
            num_tests_positive,
            num_tests_negative,
            ST_X(ST_Centroid(geom)) as longitude,
            ST_Y(ST_Centroid(geom)) as latitude,
            zip_code
        FROM philadelphia_covid_tests
        WHERE ST_Intersects(ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, geom::geography)
        LIMIT 1
    """
    )
    resp = engine.execute(zip_query, lng=lng, lat=lat).fetchone()
    if resp is not None:
        num_neg, num_pos = resp['num_tests_negative'], resp['num_tests_positive']
        num_total = num_neg + num_pos
        num_pos_per = round(num_pos/(num_total) * 100, 3)
        zip_code = resp['zip_code']
        error_m = error_message
    else: 
        num_pos_per = 'unavailable'
        zip_code = 'Not Found'
        error_m = "Sorry, we cannot retrieve the covid information assoicated with your entered address in Philadelphia.  IS IT IN PHILADELPHIA? Please try another one."
    
    return num_pos_per, zip_code, error_m

def get_nearby_test_sites(lng, lat):
    """Get Nearby Test Sites (4)"""
    test_sites_query = text(
        """
        SELECT
            testing_location_nameoperator as site_name, 
            testing_location_address as address,
            ST_Distance(ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography)::integer as dist_m,
            lng, lat
        FROM covid_testing_sites_phl
        ORDER BY dist_m
        LIMIT 3
    """
        )

    resp = engine.execute(test_sites_query, lng=lng, lat=lat).fetchall()
    return resp

# 404 page example
@app.errorhandler(404)
def page_not_found(err):
    """404 page"""
    return render_template("null_island.html", mapbox_token=MAPBOX_TOKEN), 404


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(debug=True, host="127.0.0.1", port=5004)
