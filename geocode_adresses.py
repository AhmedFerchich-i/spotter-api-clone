from geopy.geocoders import Nominatim
import pandas as pd
import os
from django.conf import settings
import requests
import time
from dotenv import load_dotenv
load_dotenv('.env')
api_token=os.getenv('OPEN_ROUTES_API_TOKEN')
geolocator = Nominatim(user_agent="ahmed")
source_file = os.getenv('SOURCE_CSV')
processed_file = os.getenv('C:\\Users\\G702578\\Desktop\\DJANGO APIS\\spotter-test\\AhmedFerchichi\\fuel-prices-for-be-assessment-clean.csv')
def convert_address(address:str):
    url = "https://api.openrouteservice.org/geocode/search"
    headers = { 'Authorization': api_token, 'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8' } 
    params = {"text": address, "boundary.country": "US"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if 'features' in data and len(data['features']) > 0:
         location = data['features'][0]['geometry']['coordinates']
         print('location ',location)
         return location[1], location[0]# Latitude, Longitude
    else:
         print(f"Geocoding failed for address: {address}, Data: {data}")
         return None, None
def convert_csv():
    headers=list(pd.read_csv(source_file).columns.values)
    df=pd.read_csv(source_file,chunksize=10)
    headers+=['Latitude','Longitude']
    pd.DataFrame(columns=headers).to_csv(source_file,index=False)
    for chunk in df:
      i=0  
      latitudes = []
      longitudes = []
      for name,address,City,State in zip(chunk['Truckstop Name'],chunk['Address'],chunk['City'],chunk['State']):
          full_address=f"{name},{address}, {City}, {State}"
          print('address ',full_address)
          lat, lon = convert_address(full_address)
          latitudes.append(lat) 
          longitudes.append(lon)
          i+=1
          print('i ',i)
      chunk['Latitude'] = latitudes
      chunk['Longitude'] = longitudes
      chunk.dropna()
      chunk.to_csv(processed_file,header=False, mode='a', index=False)
      time.sleep(10)
convert_csv()




    