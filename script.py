from dotenv import load_dotenv
from os import getenv, listdir
from os.path import isfile, join
from datetime import datetime
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import osmnx as ox
from currency_converter import CurrencyConverter

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

''' px.set_mapbox_access_token(mapbox_token)
fig = px.scatter_mapbox(eats_app_analytics_df, lat="Latitude", lon="Longitude", color="Analytics Event Type",
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
''' print("Total:", eats_order_details_df.drop_duplicates(
    subset='Order ID').order_price_euro.sum(), "EUR")
print("Prix moyen:", eats_order_details_df.drop_duplicates(
    subset='Order ID').order_price_euro.mean(), "EUR")
fig = px.histogram(eats_order_details_df.drop_duplicates(
    subset='Order ID').order_price_euro)
fig.show() '''
cum_sum_eats = eats_order_details_df.drop_duplicates(
    subset='Order ID').set_index('Order Time')
cum_sum_eats = cum_sum_eats.groupby(pd.Grouper(freq="M")).sum()
cum_sum_eats['cum_sum'] = cum_sum_eats['order_price_euro'].cumsum()
''' fig = px.line(cum_sum_eats, x=cum_sum_eats.index, y='cum_sum')
fig.show()
print(cum_sum_eats) '''

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
px.set_mapbox_access_token(mapbox_token)
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
trip_uberx_paris = trips_data_df[(trips_data_df['Product Type'].isin(
    ['UberX', 'uberX', 'Comfort', 'Star', 'UberPOP', 'uberPOOL UFP'])) & (trips_data_df['City'] == 603)]
trip_uberx_paris = trip_uberx_paris[[
    'begin_trip_hour', 'begin_weekday', "Distance (miles)", "duration", "fare_amount_euro"]]
''' print(trip_uberx_paris)
fig = px.scatter(trip_uberx_paris, x="Distance (miles)", y="fare_amount_euro", color="begin_weekday",
                 size='begin_trip_hour')
fig.show()
fig = px.scatter(trip_uberx_paris, x="Distance (miles)",
                 y="fare_amount_euro", trendline="ols")
fig.show() '''
