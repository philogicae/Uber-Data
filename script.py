import random
from dotenv import load_dotenv
from os import getenv, listdir
from os.path import isfile, join
from datetime import datetime
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import osmnx as ox
from currency_converter import CurrencyConverter
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

load_dotenv()
mypath = getenv("PATH_FOLDER")
mapbox_token = getenv("MAPBOX_TOKEN")
ox.config(use_cache=True, log_console=True)
c = CurrencyConverter()

# Profile
account = mypath + "/Account and Profile"
onlyfiles = [f for f in listdir(account) if isfile(join(account, f))]
profile_data_df = pd.read_csv(join(account, 'profile_data.csv'))
''' print(profile_data_df) '''

# Signup location
''' px.set_mapbox_access_token(mapbox_token)
fig = px.scatter_mapbox(profile_data_df, lat="Signup Lat", lon="Signup Long",
                        color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10)
fig.show() '''

# Customer support
customer_support_contacts_df = pd.read_csv(
    join(account, 'customer_support_contacts.csv'))
''' print(customer_support_contacts_df.head()) '''

# Chat
communications_sent_df = pd.read_csv(join(account, 'communications_sent.csv'))
''' print(communications_sent_df.head())
print(
    communications_sent_df.Medium.value_counts())
print(communications_sent_df.Content.tolist()) '''

# Payment
payment_methods_df = pd.read_csv(join(account, 'payment_methods-0.csv'))
''' print(payment_methods_df.head()) '''

# Eats
eats = mypath + "/Eats"
eats_app_analytics_df = pd.read_csv(join(
    eats, 'eats_app_analytics-0.csv'))
''' print(eats_app_analytics_df.head()) '''

''' fig = px.scatter_mapbox(eats_app_analytics_df, lat="Latitude", lon="Longitude", color="Analytics Event Type",
                        color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10)
fig.show() '''

# Eats orders
eats_order_details_df = pd.read_csv(join(eats, 'eats_order_details.csv'))
list_date = eats_order_details_df['Order Time'].tolist()
list_date = [datetime.strptime(date_, '%Y-%m-%d %H:%M:%S %z %Z')
             for date_ in list_date]
eats_order_details_df['Order Time'] = list_date
''' print(eats_order_details_df.head())
print(eats_order_details_df.tail(10))
print(
    f"Le plus souvent commandé : {eats_order_details_df['Item Name'].value_counts().index.tolist()[0]} a été commandé {eats_order_details_df['Item Name'].value_counts().tolist()[0]} fois")
 '''
eats_order_details_df['order_price_euro'] = ''
eats_order_details_df['Order Price'].fillna(0, inplace=True)
eats_order_details_df['Currency'].fillna('EUR', inplace=True)


def convert(row):
    row['order_price_euro'] = c.convert(
        row['Order Price'], row['Currency'], 'EUR')
    return row


eats_order_details_df = eats_order_details_df.apply(convert, axis=1)
print("Total Uber eats:", eats_order_details_df.drop_duplicates(
    subset='Order ID').order_price_euro.sum(), "EUR")
print("Prix moyen:", eats_order_details_df.drop_duplicates(
    subset='Order ID').order_price_euro.mean(), "EUR")
''' fig = px.histogram(eats_order_details_df.drop_duplicates(
    subset='Order ID').order_price_euro)
fig.show() '''
cum_sum_eats = eats_order_details_df.drop_duplicates(
    subset='Order ID').set_index('Order Time')
cum_sum_eats = cum_sum_eats.groupby(pd.Grouper(freq="M")).sum()
cum_sum_eats['cum_sum'] = cum_sum_eats['order_price_euro'].cumsum()
''' fig = px.line(cum_sum_eats, x=cum_sum_eats.index, y='cum_sum')
fig.show() '''

# Rider
rider = mypath + "/Rider"
trips_data_df = pd.read_csv(join(rider, 'trips_data.csv'))
trips_data_df = trips_data_df[trips_data_df['Trip or Order Status'] == 'COMPLETED']

list_date = trips_data_df['Begin Trip Time'].tolist()
list_date = [datetime.strptime(date_, '%Y-%m-%d %H:%M:%S %z %Z')
             for date_ in list_date]
trips_data_df['Begin Trip Time'] = list_date

list_date = trips_data_df['Dropoff Time'].tolist()
list_date = [datetime.strptime(date_, '%Y-%m-%d %H:%M:%S %z %Z')
             for date_ in list_date]
trips_data_df['Dropoff Time'] = list_date
''' print(trips_data_df.head())
print(trips_data_df.tail())
print(trips_data_df['Fare Currency'].value_counts()) '''


def convert(row):
    row['fare_amount_euro'] = c.convert(
        row['Fare Amount'], row['Fare Currency'], 'EUR')
    return row


trips_data_df['fare_amount_euro'] = ''
trips_data_df['Fare Amount'].fillna(0, inplace=True)
trips_data_df['Fare Currency'].fillna('EUR', inplace=True)
trips_data_df = trips_data_df[trips_data_df['Fare Currency'] != 'UAH']
trips_data_df = trips_data_df.apply(convert, axis=1)
''' print(trips_data_df['Product Type'].value_counts()) '''

cum_sum_rides = trips_data_df[trips_data_df['Product Type']
                              != 'UberEATS Marketplace'].set_index('Begin Trip Time')
cum_sum_rides = cum_sum_rides.groupby(pd.Grouper(freq="M")).sum()
cum_sum_rides['cum_sum'] = cum_sum_rides['fare_amount_euro'].cumsum()
cum_sum_rides['cum_sum_rides'] = cum_sum_rides['cum_sum']
cum_sum_eats['cum_sum_eats'] = cum_sum_eats['cum_sum']
combinate = pd.concat([cum_sum_rides['cum_sum_rides'],
                      cum_sum_eats['cum_sum_eats']], axis=1)
combinate.fillna(0, inplace=True)
combinate['total_cum_sum'] = combinate['cum_sum_rides'] + \
    combinate['cum_sum_eats']
''' fig = go.Figure()
fig.add_trace(go.Scatter(x=combinate.index,
              y=combinate['cum_sum_eats'], mode='lines', name='eats'))
fig.add_trace(go.Scatter(x=combinate.index,
              y=combinate['cum_sum_rides'], mode='lines', name='rides'))
fig.add_trace(go.Scatter(x=combinate.index,
              y=combinate['total_cum_sum'], mode='lines', name='total'))
fig.show()
fig = px.scatter_mapbox(trips_data_df, lat="Begin Trip Lat", lon="Begin Trip Lng", color="Distance (miles)",
                        size='fare_amount_euro', color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10)
fig.show() '''

trips_data_df['duration'] = trips_data_df['Dropoff Time'] - \
    trips_data_df['Begin Trip Time']
duration_list = []
for date in trips_data_df['duration'].tolist():
    duration_list.append(date.total_seconds()/60)
trips_data_df['duration'] = duration_list
''' fig = px.histogram(trips_data_df['duration'])
fig.show() '''

''' fig = px.scatter(trips_data_df, x="Distance (miles)", y="fare_amount_euro", color="Product Type",
                 size='duration', hover_data=['City'])
fig.show() '''

trips_data_df['Begin Trip Time'] = pd.to_datetime(
    trips_data_df['Begin Trip Time'], format='%Y-%m-%d %H:%M:%S %z %Z')
trips_data_df['begin_trip_hour'] = trips_data_df['Begin Trip Time'].dt.hour
trips_data_df['begin_weekday'] = trips_data_df['Begin Trip Time'].dt.weekday
trip_uberx = trips_data_df[(trips_data_df['Product Type'].isin(
    ['UberX', 'uberX', 'Comfort', 'Star', 'UberPOP', 'uberPOOL UFP']))]
trip_uberx = trip_uberx[[
    'begin_trip_hour', 'begin_weekday', "Distance (miles)", "fare_amount_euro"]]
''' print(trip_uberx)
fig = px.scatter(trip_uberx, x="Distance (miles)", y="fare_amount_euro", color="begin_weekday",
                 size='begin_trip_hour')
fig.show()
fig = px.scatter(trip_uberx, x="Distance (miles)",
                 y="fare_amount_euro", trendline="ols")
fig.show() '''

X_train, X_test, y_train, y_test = train_test_split(trip_uberx.drop('fare_amount_euro', axis=1),
                                                    trip_uberx['fare_amount_euro'], test_size=0.30,
                                                    random_state=101)
''' fig = px.histogram(y_train)
fig.show()
 '''
reg = LinearRegression()
reg .fit(X_train, y_train)
y_pred = reg.predict(X_test)
''' print(mean_absolute_error(y_test, y_pred))
print(X_test.head()) '''

to_pred = pd.DataFrame(
    columns=['begin_trip_hour', 'begin_weekday', 'Distance (miles)'])
values = ['18', '4', '5']
to_pred.loc[0] = values
pred = reg.predict(to_pred)
''' print(
    f'Le prix pour un UberX pour un trajet de {values[2]}miles, à {values[0]}h le {int(values[1])+1}ème jour de la semaine est de : {pred[0].round(1)}€') '''

rider_app_analytics_df = pd.read_csv(join(rider, 'rider_app_analytics-0.csv'))
''' fig = px.scatter_mapbox(rider_app_analytics_df, lat="Latitude", lon="Longitude",
                        color="Analytics Event Type", color_continuous_scale=px.colors.cyclical.IceFire, size_max=15, zoom=10)
fig.show() '''

print("Total Uber ride:", trips_data_df['fare_amount_euro'].sum(), "EUR")
print("Prix moyen:", trips_data_df['fare_amount_euro'].mean(), "EUR")

print("Total Uber:", eats_order_details_df.drop_duplicates(
    subset='Order ID').order_price_euro.sum() + trips_data_df['fare_amount_euro'].sum(), "EUR")


def create_graph(loc, dist, transport_mode, loc_type="address"):
    """Transport mode = ‘walk’, ‘bike’, ‘drive’, ‘drive_service’, ‘all’, ‘all_private’, ‘none’"""
    if loc_type == "address":
        G = ox.graph_from_address(loc, dist=dist, network_type=transport_mode)
    elif loc_type == "points":
        G = ox.graph_from_point(loc, dist=dist, network_type=transport_mode)
    return G


# Map route
''' G = create_graph("Bucuresti", 10000, "drive")
ox.plot_graph(G) '''

''' print(trips_data_df['City'].value_counts()) '''

trips_paris_df = trips_data_df[trips_data_df['City'] == 603]
lat_begin = trips_paris_df['Begin Trip Lat'].tolist()
lon_begin = trips_paris_df['Begin Trip Lng'].tolist()
lon_end = trips_paris_df['Dropoff Lng'].tolist()
lat_end = trips_paris_df['Dropoff Lat'].tolist()

''' G = create_graph("Bucuresti", 10000, "drive")
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

routes_list = []
for lat_begin_, lon_begin_, lon_end_, lat_end_ in zip(lat_begin, lon_begin, lon_end, lat_end):
    start_node = ox.distance.nearest_nodes(G, lon_begin_, lat_begin_)
    end_node = ox.distance.nearest_nodes(G, lon_end_, lat_end_)
    try:
        route = nx.shortest_path(G, start_node, end_node, weight='travel_time')
        routes_list.append(route)
    except nx.exception.NetworkXNoPath:
        pass
number_of_colors = len(routes_list)
color = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
             for i in range(number_of_colors)]
['#D11B82', '#A820E6', '#8FC3AB', '#CE0BAB', '#983DE4', '#F2966F', '#2611F4', '#9C67DB', '#D4F84E', '#328D43', '#AAA725', '#79FF8A', '#B5F431', '#C794F5', '#DA426E', '#CB35E5', '#2900BF', '#3D9201', '#443F9C', '#89C4A4', '#ABC240', '#49EDF4', '#0687D1', '#F5789D', '#CB1ACC', '#2A3705', '#39A287', '#6F6BC6', '#A121B2', '#7A688A', '#9A96FB', '#239CDC', '#102BDA', '#5E1A94', '#07488F', '#7B7BAA', '#DFF2E9', '#6E643E', '#CC234B', '#B53E76', '#216FF4', '#197F19', '#E70050', '#910D96', '#847462', '#5E3B06', '#13F9CD', '#E554B0', '#B8265D',
    '#CBDA27', '#02F102', '#648A0D', '#C74998', '#AA8742', '#7BFB14', '#BF2CCC', '#9A28DF', '#AB16A9', '#858598', '#2713CA', '#AF12F0', '#BA0B7E', '#5FAB1E', '#85ABB9', '#89F000', '#D6FB51', '#3016F2', '#DF6F96', '#83B7D9', '#786555', '#63FD64', '#2FC8BF', '#E67609', '#00AF41', '#8A869C', '#72DCA9', '#0438D2', '#151317', '#FE7443', '#6FD56F', '#72B2C7', '#A72676', '#4DE283', '#C19C31', '#4E6EFA', '#65B313', '#2640C1', '#9BA1F8', '#64409C', '#354C6D', '#98F185', '#6FB097', '#373D9A', '#CEB024', '#38E9BE', '#0D76CA', '#20901B', '#379125']
ox.plot_graph_routes(G, routes_list, route_colors=color,
                     route_linewidth=6, node_size=0, bgcolor='k', figsize=(20, 20)) '''
