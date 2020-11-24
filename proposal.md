# Final Project Proposal

MUSA 509: Geospatial Cloud Computing & Visualization

**Team Members:** Haoheng Tang, Zhijie Zhou 

## Abstract

*U.S.GoAnywhereMaskON* 

The main idea of this project is to provide users with a COVID-19 special version of "Google Map" OR "Mapbox," with two essential functions:
- One-click COVID-19 Information available at national, state, county levels - Note that the zip code level info. is only for Philadelphia city (as a miniature).
- Navigation in multiple transportation modes with list of amenities close to user's input destination location.

We would to have the user acknowledge the risk of traveling to a specific place prior to a journey. 

**Primary version**:
  - Sser-interactive covid-19 test results at multiple scales (Pop-up window when clicking on a point on the map. Users get more detailed info. and a zoom-in map by further searching.)
  - An app that features covid-19 risk assessment, amenities search, 3-in-1 (driving, cycling and walking) navigation with map, routes and detailed instructions (for Philadelphia city only).
  
**Advanced version** (if applicable, depending on actual progress):
  - User-interactive covid-19 test results at multiple scales (Pop-up window when clicking on a point on the map, zoom when clicking, etc.)
  - Extend the coverage of the navigation map to larger regions, as well as interactive points of interest inside the navigation map to provide more information and fast-response navigation to faciliate the path finding process. 

## Data Sources

Datasets of covid-test results for every zip code in Philadelphia

- Access: Yes. Data hosted in class database.
- Size of Dataset: 48 rows x 4 columns
- How to host: AWS

United States COVID-19 cases and deaths by state over time

- Access: Yes. Already have .csv file downloaded from Data.CDC.gov.
          API Endpoint: https://data.cdc.gov/resource/9mfq-cb36.json
- Size of Dataset: 18061 rows x 15 columns
- How to host: AWS


Provisional COVID-19 death counts in the United States by county

- Access: Yes. Already have .csv file downloaded from Data.CDC.gov.
          API Endpoint: https://data.cdc.gov/resource/kn79-hsxy.json
- Size of Dataset: 1346 rows x 8 columns
- How to host: AWS

OpenStreetMap (Amenities)

- Access: Yes, through BigQuery
- Size of Dataset: N/A
- How to host: BigQuery

Navigation

- Mapbox API

## Wireframe

![avatar](https://github.com/MUSA-509/final-project-haoheng-zj/blob/main/wireframe.jpg)

Available at [wireframe.jpg](https://github.com/MUSA-509/final-project-haoheng-zj/blob/main/wireframe.jpg). 

Or you can access [wireframe.ai](https://github.com/MUSA-509/final-project-haoheng-zj/blob/main/wireframe.ai) for an editable version.
