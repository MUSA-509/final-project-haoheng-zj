"""Musa 509 final project application"""
from flask import Flask, Response, render_template, escape, request, url_for
import json
import logging
import requests
import pandas as pd
from sqlalchemy import create_engine, String, Integer
from sqlalchemy.sql import text, bindparam
import geopandas as gpd
from shapely.geometry import shape
from datetime import datetime, timedelta, timezone

try:
    from geopy import distance
except ImportError:
    pass

# initialize application
application = Flask(__name__, template_folder="templates")

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

# load credentials from JSON file
HOST = pg_creds["HOST"]
USERNAME = pg_creds["USERNAME"]
PASSWORD = pg_creds["PASSWORD"]
DATABASE = pg_creds["DATABASE"]
PORT = pg_creds["PORT"]


def get_sql_engine():
    """Generates a SQLAlchemy engine"""
    return create_engine(f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}")


# activate the SQLAlchemy engine
engine = get_sql_engine()


@application.route("/")
def index():
    """User input page"""
    covidStats = get_national_covid_stats("12/20/2020")
    return Response(render_template("index.html", tot_cases=covidStats[0], tot_death=covidStats[1]), 200, mimetype="text/html")


@application.route("/dest_info")
def dest_info():
    """Landing page"""
    address = get_address(request.args)
    error_message = None

    if address is not None:
        geocoded = geocoding(address).json()

        # check if the geocoding results contain 'features'
        if geocoded["features"]:
            lng, lat = geocoded["features"][0]["geometry"]["coordinates"]
        else:
            error_message = (
                f"Invalid address entered ({address}). Here we set Meyerson Hall, University of Pennsylvania, as the default destination."
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
   
    directions_resp = get_direction(PHL_CITY_HALL_LNG, PHL_CITY_HALL_LAT, lng, lat).json()

    if directions_resp["code"] == 'Ok':
        route_info = get_route(directions_resp)

    else:
        error_message = (f"Sorry we cannot retrieve the directions data to your destination ({address}). MapBox Direction API says 'Route exceeds maximum distance limitation.' Here we show the directions to Meyerson Hall. Can you specify another one or choose one from the drop-down menu?")
        directions_resp_Meyerson = get_direction(PHL_CITY_HALL_LNG, PHL_CITY_HALL_LAT, MEYERSON_LNG, MEYERSON_LAT).json()
        route_info = get_route(directions_resp_Meyerson)
        address = 'Meyerson Hall, University of Pennsylvania'


    html_map = render_template(
        "destination_info.html",
        mapbox_token=MAPBOX_TOKEN,
        curr_time=curr_time,num_pos_per=num_pos_per,zip_code=zip_code,
        test_sites = test_sites,

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
            geojson_str=route_info[0], instr=route_info[1], dir_data=route_info[2], dir_duration=route_info[3],
            address=address,
            mapbox_token=MAPBOX_TOKEN
            )
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
    """Geocodes the user entered address"""
    geocoding_call = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json"
        )
    resp = requests.get(geocoding_call, params={"access_token": MAPBOX_TOKEN})
    return resp


def distance_from(lng, lat):
    """Calculates the distance from origin location"""
    return round(distance.distance((PHL_CITY_HALL_LAT, PHL_CITY_HALL_LNG), (lat, lng)).km, 2)


def get_current_time():
    """Retrieves the current time"""
    curr_time_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    curr_time_est = curr_time_utc.astimezone(timezone(timedelta(hours=-5))).strftime("%B %d, %Y %I:%M %p")
    return curr_time_est


def get_direction(ori_lng, ori_lat, dest_lng, dest_lat):
    """Retrieve directions using MapBox Direction API"""
    directions_resp = requests.get(
        f"https://api.mapbox.com/directions/v5/mapbox/driving/{ori_lng},{ori_lat};{dest_lng},{dest_lat}",
        params={
            "access_token": MAPBOX_TOKEN,
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "false",
        },
    )
    return directions_resp


def get_route(directions_resp):
    """Tidy the returned values from MapBox Directions API"""
    dir_duration = directions_resp["routes"][0]['duration']
    dir_data = pd.DataFrame(directions_resp["routes"][0]["legs"])
    dir_data = dir_data.iloc[:1].to_json()

    instruction=[]
    for step in directions_resp['routes'][0]['legs'][0]['steps']:
        instruction.append(f"{step['maneuver']['instruction']}")
    listToStr = '<br>'.join(map(str, instruction))

    routes = gpd.GeoDataFrame(
        geometry=[
            shape(directions_resp["routes"][idx]["geometry"])
            for idx in range(len(directions_resp["routes"]))
        ]
    )   
    geojson_str = routes.iloc[:1].to_json()

    return geojson_str, listToStr, dir_data, dir_duration


def get_national_covid_stats(time_input):
    """Get Covid Statistics for U.S"""
    query = text(
        """
        SELECT sum(tot_cases) as tc, sum(tot_death) as td
        FROM state_covid_tests_by_1220
        WHERE submission_date = :time_query
        """
        )
    resp = engine.execute(query, time_query=time_input).fetchone()
    cases = resp['tc']
    death = resp['td']
    return cases, death


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
    """Get Nearby Test Sites"""
    test_sites_query = text(
        """
        SELECT
            c.testing_location_nameoperator as site_name, 
            c.testing_location_address as address,
            ST_Distance(ST_SetSRID(ST_MakePoint(c.lng, c.lat), 4326)::geography, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography)::integer as dist_m,
            ST_SetSRID(ST_MakePoint(c.lng, c.lat), 4326)::geography as geom,
            c.provider_url
        FROM covid_testing_sites_phl as c
        WHERE c.provider_url is not NULL
        ORDER BY dist_m
        LIMIT 4
    """
        )
    sites = engine.execute(test_sites_query, lng=lng, lat=lat).fetchall()
    # sites = gpd.read_postgis(test_sites_query, con=engine, geom_col='geom', params={"lng":lng,"lat":lat})
    return sites


@application.route("/test_sites_download", methods=["GET"])
def test_sites_download():
    """Download GeoJSON of data snapshot - test sites"""
    address = get_address(request.args)
    geocoded = geocoding(address).json()
    lng, lat = geocoded["features"][0]["geometry"]["coordinates"]
    testSites = get_nearby_test_sites(lng, lat)
    df = pd.DataFrame(testSites)
    return Response(df.to_json(), 200, mimetype="application/json")


@application.route("/directions_download", methods=["GET"])
def directions_download():
    """Download GeoJSON of data snapshot - directions"""
    address = get_address(request.args)
    geocoded = geocoding(address).json()
    lng, lat = geocoded["features"][0]["geometry"]["coordinates"]
    directions = get_direction(PHL_CITY_HALL_LNG, PHL_CITY_HALL_LAT, lng, lat)[0]
    return Response(directions, 200, mimetype="application/json")


@application.route("/map_zip")
def map_zip():
    """covid map at zipcode level"""
    return Response(render_template("covidbyzipcode.html"), 200, mimetype="text/html")


@application.route("/map_zip_dark")
def map_zip_dark():
    """covid map at zipcode level (dark version)"""
    return Response(render_template("covidbyzipcode_dark.html"), 200, mimetype="text/html")


@application.route("/map_state")
def map_state():
    """covid map at state level"""
    return Response(render_template("covidbystate.html"), 200, mimetype="text/html")


@application.route("/map_state_dark")
def map_state_dark():
    """covid map at state level (dark version)"""
    return Response(render_template("covidbystate_dark.html"), 200, mimetype="text/html")


@application.route("/map_county")
def map_county():
    """covid map at county level"""
    return Response(render_template("covidbycounty.html"), 200, mimetype="text/html")


@application.route("/map_county_dark")
def map_county_dark():
    """covid map at county level (dark version)"""
    return Response(render_template("covidbycounty_dark.html"), 200, mimetype="text/html")


@application.route("/covid_state")
def covid_state():
    """covid map at zipcode level (trigger)"""
    return Response(render_template("covid_state.html"), 200, mimetype="text/html")


@application.route("/covid_county")
def covid_county():
    """covid map at zipcode level (trigger)"""
    return Response(render_template("covid_county.html"), 200, mimetype="text/html")


@application.route("/covid_zip")
def covid_zip():
    """covid map at zipcode level (trigger)"""
    return Response(render_template("covid_zip.html"), 200, mimetype="text/html")


# 404 page example
@application.errorhandler(404)
def page_not_found(err):
    """404 page"""
    return render_template("null404page.html", mapbox_token=MAPBOX_TOKEN), 404


if __name__ == "__main__":
    application.jinja_env.auto_reload = True
    application.config["TEMPLATES_AUTO_RELOAD"] = True
    application.run(debug=True)
