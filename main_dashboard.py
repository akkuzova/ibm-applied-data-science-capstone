import streamlit as st
import requests
import pandas as pd
import numpy as np
import datetime
import os

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
st.set_page_config(layout="wide")
api_base_url = 'https://api.spacexdata.com/v4/'
data_directory = './app_data/'


def download_api_data():
    spacex_url = api_base_url + "launches/past"
    response = requests.get(spacex_url)
    data = pd.json_normalize(response.json())

    data = data[['rocket', 'payloads', 'launchpad', 'cores', 'flight_number', 'date_utc']]

    data = data[data['cores'].map(len) == 1]
    data = data[data['payloads'].map(len) == 1]

    data['cores'] = data['cores'].map(lambda x: x[0])
    data['payloads'] = data['payloads'].map(lambda x: x[0])

    data['date'] = pd.to_datetime(data['date_utc']).dt.date
    data = data[data['date'] <= datetime.date(2020, 11, 13)]

    launch_details = get_launch_details(data)
    launch_details['flight_number'] = list(data['flight_number'])
    launch_details['date'] = list(data['date'])

    df = pd.DataFrame.from_dict(launch_details)

    df = df[df['booster_version'] != 'Falcon 1']
    data_falcon9 = df

    data_falcon9.loc[:, 'flight_number'] = list(range(1, data_falcon9.shape[0] + 1))
    data_falcon9.isnull().sum()

    payload_mass_mean = data_falcon9['payload_mass'].astype('float').mean(axis=0)

    data_falcon9['payload_mass'].replace(np.nan, payload_mass_mean, inplace=True)

    data_falcon9['payload_mass'].isnull().sum()

    st.dataframe(data_falcon9)
    save_dataframe(data_falcon9)


def save_dataframe(data_falcon9):
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)
    data_falcon9.to_csv(data_directory + 'dataset_part_1.csv', index=False)


def get_launch_details(data):
    launch_details = {'launch_site': [], 'longitude': [], 'latitude': [], 'payload_mass': [], 'orbit': [],
                      'booster_version': [], 'block': [], 'reused_count': [], 'serial': [], 'outcome': [],
                      'flights': [], 'grid_fins': [], 'reused': [], 'legs': [], 'landing_pad': []}
    expected_rows_count = len(data)

    st.write(f'Getting Booster Version Information From {api_base_url}rockets/ ...')
    booster_bar = st.progress(0)
    for x in data['rocket']:
        if x:
            response = requests.get(api_base_url + "rockets/" + str(x)).json()
            launch_details['booster_version'].append(response['name'])
            booster_bar.progress(len(launch_details['booster_version']) / expected_rows_count)

    st.write(f'Getting Launch Site Information From {api_base_url}launchpads/ ...')
    launch_bar = st.progress(0)
    for x in data['launchpad']:
        if x:
            response = requests.get(api_base_url + "launchpads/" + str(x)).json()
            launch_details['longitude'].append(response['longitude'])
            launch_details['latitude'].append(response['latitude'])
            launch_details['launch_site'].append(response['name'])
            launch_bar.progress(len(launch_details['launch_site']) / expected_rows_count)

    st.write(f'Getting Payload Mass Information From {api_base_url}payloads/ ...')
    launch_bar = st.progress(0, text='0%')
    for load in data['payloads']:
        if load:
            response = requests.get(api_base_url + "payloads/" + load).json()
            launch_details['payload_mass'].append(response['mass_kg'])
            launch_details['orbit'].append(response['orbit'])
            launch_bar.progress(len(launch_details['orbit']) / expected_rows_count)

    st.write(f'Getting Core Information From {api_base_url}/cores ...')
    core_bar = st.progress(0)
    for core in data['cores']:
        if core['core'] is not None:
            response = requests.get(api_base_url + "cores/" + core['core']).json()
            launch_details['block'].append(response['block'])
            launch_details['reused_count'].append(response['reuse_count'])
            launch_details['serial'].append(response['serial'])
        else:
            launch_details['block'].append(None)
            launch_details['reused_count'].append(None)
            launch_details['serial'].append(None)
        launch_details['outcome'].append(str(core['landing_success']) + ' ' + str(core['landing_type']))
        launch_details['flights'].append(core['flight'])
        launch_details['grid_fins'].append(core['gridfins'])
        launch_details['reused'].append(core['reused'])
        launch_details['legs'].append(core['legs'])
        launch_details['landing_pad'].append(core['landpad'])
        core_bar.progress(len(launch_details['landing_pad']) / expected_rows_count)

    return launch_details


st.header('SpaceX Falcon 9 Launches Analytics Dashboard')
st.button(label='Download Data From SpaceX API', on_click=download_api_data)
