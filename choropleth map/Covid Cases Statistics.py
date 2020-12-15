from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
import altair as alt

pd.options.display.max_columns = 999

plt.rcParams['figure.figsize'] = (10,6)

import folium

## Covid by state-------------------------------------

tile_url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}{r}.png'
attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

url = "https://opendata.arcgis.com/datasets/1612d351695b467eba75fdf82c10884f_0.geojson"
states = gpd.read_file(url).rename(columns={"NAME":"State"})

def get_state_style(feature):
    """Return a style dict."""
    return {"weight": 2, "color": "lightblue", "fillOpacity": 0.1}


def get_highlighted_style(feature):
    """Return a style dict when highlighting a feature."""
    return {"weight": 2, "color": "red"}

import json

with open("pg-credentials.json") as creds:
    creds = json.load(creds)

PASSWORD = creds["PASSWORD"]
HOST = creds["HOST"]
USERNAME = creds["USERNAME"]
DATABASE = creds["DATABASE"]
PORT = creds["PORT"]


from sqlalchemy import create_engine

engine = create_engine(f"postgresql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}")

from sqlalchemy.sql import text
from pandas.core.frame import DataFrame

def covid_cases_state(index):
    query = text("""
      SELECT * 
      FROM public.state_covid_tests_by_1204
      WHERE index=:index
    """)

    resp = engine.execute(query, index=index)
    if resp.rowcount > 0:
        return resp.fetchall()
    if resp.rowcount > 0:
        return resp.fetchall()
    return print("There is no index\""+str(index)+".")

num=0
df = pd.DataFrame(covid_cases_state(num))
num=1
while num < 60:
    add = pd.DataFrame(covid_cases_state(num))
    df = df.append(add, ignore_index = True)
    num = num+1

df = df.rename(columns={0: "index", 1: "date", 2: "STATE_ABBR", 3: "tot_cases", 4: "conf_cases",
                   5: "prob_cases", 6: "new_case", 7: "pnew_case", 8: "tot_death", 9: "conf_death",
                   10: "prob_death", 11: "new_death", 12: "pnew_death", 13: "created_at", 14: "constant_cases",
                   15: "consent_deaths"})

covid_state = states.merge(df, on='STATE_ABBR')

states_geojson = states.to_crs(epsg=4326).to_json()

tile_url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}{r}.png'
attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

def get_state_style(feature):
    """Return a style dict."""
    return {"weight": 0, "color": "grey", "fillOpacity": 0}


def get_highlighted_style(feature):
    """Return a style dict when highlighting a feature."""
    return {"weight": 1.6, "color": "white","fillOpacity": 0.4}

# Create the map
m = folium.Map(
    location=[36.99, -95.13],
    zoom_start=5,
    tiles=tile_url,
    attr=attr
)

# light mode
folium.Choropleth(
    geo_data=states_geojson, 
    data=covid_state, 
    columns=["FID", 'tot_cases'], 
    key_on="feature.properties.FID", 
    fill_color='RdPu', 
    fill_opacity=0.7,
    line_opacity=1,
    line_weight=1.32,
    line_color="#FFFFFF",
    legend_name='Total cases by state',
    name='choropleth',
).add_to(m)

folium.GeoJson(
    covid_state.to_crs(epsg=4326).to_json(),
    name='U.S. States',
    style_function=get_state_style,
    highlight_function=get_highlighted_style,
    tooltip=folium.GeoJsonTooltip(['State','tot_cases'])
).add_to(m)

# Also add option to toggle layers
folium.LayerControl().add_to(m)

m

#dark mode
tile_url = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

def get_state_style(feature):
    """Return a style dict."""
    return {"weight": 0, "color": "grey", "fillOpacity": 0}


def get_highlighted_style(feature):
    """Return a style dict when highlighting a feature."""
    return {"weight": 1.6, "color": "white","fillOpacity": 0.4}

# Create the map
m = folium.Map(
    location=[36.99, -95.13],
    zoom_start=5,
    tiles=tile_url,
    attr=attr
)

folium.Choropleth(
    geo_data=states_geojson, 
    data=covid_state, 
    columns=["FID", 'tot_cases'], 
    key_on="feature.properties.FID", 
    fill_color='YlOrBr', 
    fill_opacity=0.86,
    line_opacity=1,
    line_weight=1.32,
    line_color="#FFFFFF",
    legend_name='Total cases by state',
    name='choropleth',
).add_to(m)

folium.GeoJson(
    covid_state.to_crs(epsg=4326).to_json(), # IMPORTANT: make sure CRS is lat/lng (EPSG=4326)
    name='U.S. States',
    style_function=get_state_style,
    highlight_function=get_highlighted_style,
    tooltip=folium.GeoJsonTooltip(['State','tot_cases'])
).add_to(m)

# Also add option to toggle layers
folium.LayerControl().add_to(m)

m

## Covid by county-------------------------------------------------------

url2= "https://opendata.arcgis.com/datasets/50c2b19df296459fad5f975bb129950f_0.geojson"
Penn = gpd.read_file(url2)

Penn['COUNTY_NAME']= Penn['COUNTY_NAME'].str.lower()
Penn['COUNTY_NAME']= Penn['COUNTY_NAME'].str.title()
Penn = Penn.rename(columns={"COUNTY_NAME": "County_Name"})
Penn.head()

def covid_cases_county(index):
    query = text("""
      SELECT * 
      FROM public.penn_county_covid_by_1204
      WHERE index=:index
    """)

    resp = engine.execute(query, index=index)
    if resp.rowcount > 0:
        return resp.fetchall()
    if resp.rowcount > 0:
        return resp.fetchall()
    return print("There is no index\""+str(index)+".")

num=0
countydf = pd.DataFrame(covid_cases_county(num))
num=1
while num < 60:
    add = pd.DataFrame(covid_cases_county(num))
    countydf = countydf.append(add, ignore_index = True)
    num = num+1


countydf = countydf.rename(columns={0: "index", 1: "County_Name", 2: "Date", 3: "New_Cases", 4: "Seven_Day_Average New Cases",
                   5: "Cumulative_Cases", 6: "Population_2018", 7: "New_Case_Rate", 8: "Seven_Day_Average_New_Case_Rate", 9: "Cumulative_Case_Rate",
                   10: "New_Deaths", 11: "Seven_Day_Average_New_Deaths", 12: "Total_Deaths", 13: "New_Deaths_Rate", 14: "Seven_Day_Average_New_Death_Rate",
                   15: "Total_Death_Rate"})

covid_county = Penn.merge(countydf, on='County_Name', how="left")
covid_county.head()

covid_county['Cumulative_Cases'] = covid_county['Cumulative_Cases'].fillna(0, inplace=False)
len(covid_county)

county_geojson = Penn.to_crs(epsg=4326).to_json()
tile_url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}{r}.png'
attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

def get_county_style(feature):
    """Return a style dict."""
    return {"weight": 0, "color": "grey", "fillOpacity": 0}


def get_highlighted_style(feature):
    """Return a style dict when highlighting a feature."""
    return {"weight": 1.6, "color": "white","fillOpacity": 0.4}

# light mode
m = folium.Map(
    location=[40.99, -77.73],
    zoom_start=8,
    tiles=tile_url,
    attr=attr
)

folium.Choropleth(
    geo_data=county_geojson, 
    data=covid_county, 
    columns=["COUNTY_CODE", 'Cumulative_Cases'], 
    key_on="feature.properties.COUNTY_CODE", 
    fill_color='RdPu', 
    fill_opacity=0.93,
    line_opacity=1,
    line_weight=1.32,
    line_color="#FFFFFF",
    legend_name='Total cases by County',
    name='choropleth',
).add_to(m)

folium.GeoJson(
    covid_county.to_crs(epsg=4326).to_json(), # IMPORTANT: make sure CRS is lat/lng (EPSG=4326)
    name='Pennsylvania',
    style_function=get_county_style,
    highlight_function=get_highlighted_style,
    tooltip=folium.GeoJsonTooltip(['County_Name','Cumulative_Cases'])
).add_to(m)

# Also add option to toggle layers
folium.LayerControl().add_to(m)

m

#dark mode
tile_url = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

# Create the map
m = folium.Map(
    location=[40.99, -77.73],
    zoom_start=8,
    tiles=tile_url,
    attr=attr
)

folium.Choropleth(
    geo_data=county_geojson, 
    data=covid_county, 
    columns=["COUNTY_CODE", 'Cumulative_Cases'], 
    key_on="feature.properties.COUNTY_CODE", 
    fill_color='YlOrBr', 
    fill_opacity=0.89,
    line_opacity=1,
    line_weight=1.32,
    line_color="#FFFFFF",
    legend_name='Total cases by County',
    name='choropleth',
).add_to(m)

folium.GeoJson(
    covid_county.to_crs(epsg=4326).to_json(), # IMPORTANT: make sure CRS is lat/lng (EPSG=4326)
    name='Pennsylvania',
    style_function=get_county_style,
    highlight_function=get_highlighted_style,
    tooltip=folium.GeoJsonTooltip(['County_Name','Cumulative_Cases'])
).add_to(m)

# Also add option to toggle layers
folium.LayerControl().add_to(m)

m

## Covid by zip code-------------------------------------------------------------
zip_url = "http://data.phl.opendata.arcgis.com/datasets/b54ec5210cee41c3a884c9086f7af1be_0.geojson"
zip_codes = gpd.read_file(zip_url).rename(columns={"CODE":"ZIP Code"})

zip_codes=zip_codes.rename(columns={"ZIP Code": "zip_code"})

def covid_cases_zipcode(index):
    query = text("""
SELECT * FROM public.philadelphia_covid_tests
      WHERE index=:index
    """)

    resp = engine.execute(query, index=index)
    if resp.rowcount > 0:
        return resp.fetchall()
    if resp.rowcount > 0:
        return resp.fetchall()
    return print("There is no index\""+str(index)+".")

num=0
zipcodedf = pd.DataFrame(covid_cases_zipcode(num))
num=1
while num < 48:
    add = pd.DataFrame(covid_cases_zipcode(num))
    zipcodedf = zipcodedf.append(add, ignore_index = True)
    num = num+1

zipcodedf = zipcodedf.rename(columns={0: "index", 1: "geom", 2: "zip_code", 3: "num_tests_negative", 4: "num_tests_positive"})
zipcodedf = zipcodedf.drop(['geom'], axis=1)

zip_codes['zip_code'] = zip_codes['zip_code'].astype(str)
zipcodedf['zip_code'] = zipcodedf['zip_code'].astype(str)

covid_zipcode = zip_codes.merge(zipcodedf, on='zip_code', how='left')
covid_zipcode.head()

covid_zipcode['num_tests_positive'] = covid_zipcode['num_tests_positive'].fillna(0, inplace=False)

zipcode_geojson = zip_codes.to_crs(epsg=4326).to_json()
tile_url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}{r}.png'
attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

def get_zipcode_style(feature):
    """Return a style dict."""
    return {"weight": 0, "color": "grey", "fillOpacity": 0}


def get_highlighted_style(feature):
    """Return a style dict when highlighting a feature."""
    return {"weight": 1.6, "color": "white","fillOpacity": 0.4}

#light mode
m = folium.Map(
    location=[40.00, -75.10],
    zoom_start=11.5,
    tiles=tile_url,
    attr=attr
)

folium.Choropleth(
    geo_data=zipcode_geojson, 
    data=covid_zipcode, 
    columns=["OBJECTID", 'num_tests_positive'], 
    key_on="feature.properties.OBJECTID", 
    fill_color='RdPu', 
    fill_opacity=0.7,
    line_opacity=1,
    line_weight=1.32,
    line_color="#FFFFFF",
    legend_name='Total cases by zip code',
    name='choropleth',
).add_to(m)

folium.GeoJson(
    covid_zipcode.to_crs(epsg=4326).to_json(), # IMPORTANT: make sure CRS is lat/lng (EPSG=4326)
    name='Philadelphia',
    style_function=get_zipcode_style,
    highlight_function=get_highlighted_style,
    tooltip=folium.GeoJsonTooltip(['zip_code','num_tests_positive'])
).add_to(m)

# Also add option to toggle layers
folium.LayerControl().add_to(m)

m

#dark mode
tile_url = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
attr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'

m = folium.Map(
    location=[40.00, -75.10],
    zoom_start=11.5,
    tiles=tile_url,
    attr=attr
)

folium.Choropleth(
    geo_data=zipcode_geojson, 
    data=covid_zipcode, 
    columns=["OBJECTID", 'num_tests_positive'], 
    key_on="feature.properties.OBJECTID", 
    fill_color='YlOrBr', 
    fill_opacity=0.76,
    line_opacity=1,
    line_weight=1.32,
    line_color="#FFFFFF",
    legend_name='Total cases by zip code',
    name='choropleth',
).add_to(m)

folium.GeoJson(
    covid_zipcode.to_crs(epsg=4326).to_json(), # IMPORTANT: make sure CRS is lat/lng (EPSG=4326)
    name='Philadelphia',
    style_function=get_zipcode_style,
    highlight_function=get_highlighted_style,
    tooltip=folium.GeoJsonTooltip(['zip_code','num_tests_positive'])
).add_to(m)

# Also add option to toggle layers
folium.LayerControl().add_to(m)

m


## Chart------------------------------------------------------------------
def covid_cases_state_week(index):
    query = text("""
      SELECT * 
      FROM public.state_case_1203_1209
      WHERE index=:index
    """)

    resp = engine.execute(query, index=index)
    if resp.rowcount > 0:
        return resp.fetchall()
    if resp.rowcount > 0:
        return resp.fetchall()
    return print("There is no index\""+str(index)+".")

num=0
stateweekdf = pd.DataFrame(covid_cases_state_week(num))
num=1
while num < 420:
    add = pd.DataFrame(covid_cases_state_week(num))
    stateweekdf = stateweekdf.append(add, ignore_index = True)
    num = num+1

stateweekdf = stateweekdf.rename(columns={0: "index", 1: "submission_date", 2: "state", 3: "tot_cases", 4: "conf_cases",
                                           5:"prob_cases",6:"new_case", 7:"pnew_case", 8:"tot_death", 9:"conf_death",10:"prob_death",
                                           11: "new_death", 12:"pnew_death",13:"created_at",14:"consent_cases",15:"consent_deaths"})

stateweeksum = stateweeksum.groupby(['submission_date'],as_index=False).sum()
stateweeksum = stateweeksum.loc[:,['submission_date','tot_cases','new_case','tot_death','new_death']]

import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1)
fig.suptitle('In the latest week')

ax1.plot(stateweeksum['submission_date'], stateweeksum['new_case'], 'o-')
ax1.set_ylabel('New cases')

ax2.plot(stateweeksum['submission_date'], stateweeksum['new_death'], 'o-')
ax2.set_xlabel('Date')
ax2.set_ylabel('New deaths')

plt.show()