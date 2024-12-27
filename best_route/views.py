from django.http import JsonResponse,HttpRequest
import requests
import pandas as pd 
from geopy.distance import distance,geodesic
import os
from django.conf import settings
from dotenv import load_dotenv
load_dotenv('.env')
api_token=os.getenv('OPEN_ROUTES_API_TOKEN')
def get_route(request:HttpRequest):
    
    start_location=request.GET.get('start')
    finish_location=request.GET.get('finish')
    if not start_location:
        return(JsonResponse({'error': 'Start  location is required.'}, status=400))
    if not finish_location:
        return(JsonResponse({'error': 'finish  location is required.'}, status=400))
    if not finish_location and not start_location:
        return(JsonResponse({'error':'finish location and start location are required'}))
    openrouteservice_url = 'https://api.openrouteservice.org/v2/directions/driving-car'
    print('api token ',api_token)
    headers = { 'Authorization': api_token  }
    params = {  'start': start_location, 'end': finish_location,'profile':'driving-car' }
    try :
     response = requests.get(openrouteservice_url,headers=headers, params=params)
     print('response ',response.content)
     route_data = response.json()
    except Exception as e:
       print(e)
       return JsonResponse({'error':'failed to fetch route data'},status=400)
    try:
     total_distance_miles=calculate_route_distance(route_data)
     print('total distance ',total_distance_miles)
    #print('response data ',route_data)
     result={'route_data':route_data}
     df=get_fuel_stops_coordinates_and_prices()
     route_coordinates=get_route_coordinates(route_data)
     #print('route coordinates ',route_coordinates)
     adress_list,price_list,latitude_coordinate_list,longitude_coordinate_list=extract_adress_and_price(df)
     print('adress and price extracted from file')
     
     
     

     adress_list,price_list,latitude_coordinate_list,longitude_coordinate_list=get_fuel_stops_along_route(adress_list,price_list,latitude_coordinate_list,longitude_coordinate_list,route_coordinates)
     if len(adress_list)==0:
        return JsonResponse({'message':'no stops were found along route'})
     print('fuel stops along route ',adress_list)
     start_lon,start_lat=start_location.split(',')
     start=(start_lat,start_lon)
     stops_address_list,stops_lat_list,stops_lon_list,stops_price_list,consecutive_distances=get_stops(start,adress_list,price_list,latitude_coordinate_list,longitude_coordinate_list,total_distance_miles)
     print('adress list ordered ',adress_list,'price list ',price_list)
     cost=calculate_fuel_cost(consecutive_distances,stops_price_list)
     result['stops']=stops_address_list
     result['cost']=cost
     return JsonResponse(result)
    except Exception as e:
       return JsonResponse({'error':'internal server error'},status=400 )


def generate_static_maps(start,stop,stops_lat,stops_lon):
   pass

def get_stops(start_location,adress_list,price_list,latitude_coordinate_list,longitude_coordinate_list,dist_max):
   print('begin get stops')
   distance_accumulated=0
   print('distance ',distance_accumulated, 'dist max ',dist_max)
   while int(distance_accumulated)<int(dist_max):
    
    price=price_list[0]
    tmp_adress_list=[]
    tmp_price_list=[]
    tmp_lat_list=[]
    tmp_lon_list=[]
    consecutive_distances=[]
    index=0
    i=0
    start=start_location
    print('start ',start)
    print('len address list ',len(adress_list))
    if len(adress_list)>0:
     while i<len(adress_list) :
        print('i ',i)
        stop=(latitude_coordinate_list[i],longitude_coordinate_list[i])
        print('stop ',stop)
        try:
         d=geodesic(start,stop).miles
         print('d ',d)
        except Exception as e:
           print(str(e))

       
        if int(d)<=500 and float(price_list[i])<float(price):
           price=price_list(i)
           print('price ',price)
           index=i
        i+=1
     tmp_price_list.append(price)
     print('len tmp price list ',len(tmp_price_list))
     tmp_adress_list.append(adress_list[index])
     print('len tmp address list ',len(tmp_adress_list))
     tmp_lat_list.append(latitude_coordinate_list[index])
     print('len lat coord list',len(latitude_coordinate_list))
     tmp_lon_list.append(longitude_coordinate_list[index])
     consecutive_distances.append(d)
     print('len lon coord list  ',len(longitude_coordinate_list))
     try:
      distance_accumulated=geodesic(start,(longitude_coordinate_list[index],latitude_coordinate_list[index])).miles
      print(' distance accumulated ',distance_accumulated)
      start=(latitude_coordinate_list[index],longitude_coordinate_list[index])
      print('start ',start)
     except Exception as e:
        print(str(e))
   
   
     for l in (adress_list,price_list,latitude_coordinate_list,longitude_coordinate_list):
        print('index ',index)
        print('l index ',l[index])
        print('l',l)
        del l[index]
    print('return ',tmp_adress_list,tmp_lat_list,tmp_lon_list,tmp_price_list)
    print('end get stops function ')
    return tmp_adress_list,tmp_lat_list,tmp_lon_list,tmp_price_list,consecutive_distances

   
   
   
   

      
def get_fuel_stops_coordinates_and_prices():
    df=pd.read_csv(os.path.join(settings.BASE_DIR,'fuel-prices-for-be-assessment-clean.csv'))
    
    return df

def get_route_coordinates(route_data):
    coordinates = route_data['features'][0]['geometry']['coordinates']
    return coordinates
def calculate_route_distance(route_data):
    total_distance_meters = route_data['features'][0]['properties']['summary']['distance']
    total_distance_miles = total_distance_meters / 1609.34 
    return total_distance_miles
def extract_adress_and_price(df):
    
    adress_list=df['Address'].to_list()
    latitude_coordinate_list=df['Latitude'].to_list()
    longitude_coordinate_list=df['Longitude'].to_list()
    price_list=df['Retail Price'].to_list()
  
   
    return adress_list,price_list,latitude_coordinate_list,longitude_coordinate_list
def check_proximity(lon,lat,route_coordinates):
    print('begin check prox ')
    max_dist_km=1
    
    try:
     for route_coord in route_coordinates:
      print('lat ',lat)
      print('lon ',lon)
      route_lon,route_lat=route_coord
      print('route lat ',route_lat, ' route lon ',route_lon)
      #print('route coord ',route_coord,'dist ',distance((lat, lon), (route_lat,route_lon)).miles)
      
      #print('distance ',distance((lat, lon), (route_lat,route_lon)).km)
      print('aa')
      if geodesic((lat, lon), (route_lat,route_lon)).km <=max_dist_km:
         
         return True
     
     return False
    except Exception as e:
        print('exception in check prox ',str(e))
        return False
def get_fuel_stops_along_route(adress_list:list,price_list:list,latitude_coordinate_list:list,longitude_coordinate_list:list,route_coordinates):
    near_adress_list=[]
    near_price_list=[]
    near_latitude_coordinate_list=[]
    near_longitude_coordinate_list=[]
    
    for adress,price,lat,lon in zip(adress_list,price_list,latitude_coordinate_list,longitude_coordinate_list):
        print('lon passed to check prox ',lon,' lat passed ',lat)
        if check_proximity(lon,lat,route_coordinates):
            near_adress_list.append(adress)
            near_price_list.append(price)
            near_latitude_coordinate_list.append(lat)
            near_longitude_coordinate_list.append(lon)
    
    return near_adress_list,near_price_list,near_latitude_coordinate_list,near_longitude_coordinate_list




def check_initial_stop_condition(lat,lon,start_location):
   max_dist=500
   print('zzz')
   d=int(distance((lon, lat)).miles)
   print('d ' , d)
   if d <=int(max_dist):
         return True
   else:
      return False
   
def check_along_route_stop_choice_validity(lat,lon,previous_lat,previous_lon,fuel_state_gallons):
   return distance((lon,lat),(previous_lon,previous_lat))>=fuel_state_gallons*10*1.60934

def calculate_fuel_cost(consectuitve_distances,price_list):
   cost=0
   for distance,price_per_gallon in zip(consectuitve_distances,price_list):
      cost+=(distance/10)*price_per_gallon
   return cost
      