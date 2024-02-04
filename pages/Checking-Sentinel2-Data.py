import geedim as gd
import streamlit as st
import pandas as pd
import ee
from datetime import date

st.set_page_config(
    layout='wide'
)

# Das Cisanggarung
roi = ee.FeatureCollection('users/idoandifyfirdaus/RoI/DasCisanggarung')
geometry = roi.geometry()

col1,col2,col3,col4 = st.columns([1,1,1,1])
with col2:
    start_date = st.date_input('Start Date', date(2023,1,1), key='start_date')

with col3:
    end_date = st.date_input('End Date', key='end_date')

col5,col6,col7 = st.columns([1,2,1])

with col6:
    st.selectbox('Select the Geometry', options=['DAS Cisanggarung'], key='geometry')

@st.cache_data
def loadData(start_date,end_date):
    if st.session_state['geometry'] == 'DAS Cisanggarung':
        geometry = ee.FeatureCollection('users/idoandifyfirdaus/RoI/DasCisanggarung').geometry()

    images = (gd.MaskedCollection.from_name('COPERNICUS/S2_SR_HARMONIZED')
                .search(str(start_date), str(end_date), geometry, cloudless_portion=0))
    
    data = images.properties

    df = pd.DataFrame.from_dict(data, orient='index')
    df['system:time_start'] = pd.to_datetime(df['system:time_start'],unit='ms').dt.strftime('%Y-%m-%d')
    df.set_index('system:time_start', inplace=True)
    df.index.set_names('DATE', inplace=True)

    # Menentukan kolom yang akan diubah presisinya
    columns_to_round = ['CLOUDLESS_PORTION', 'FILL_PORTION', 'MEAN_INCIDENCE_AZIMUTH_ANGLE_B1',
                        'MEAN_INCIDENCE_ZENITH_ANGLE_B1', 'MEAN_SOLAR_AZIMUTH_ANGLE', 'MEAN_SOLAR_ZENITH_ANGLE']

    # Menggunakan metode round untuk merubah nilai dengan presisi dua desimal
    df[columns_to_round] = df[columns_to_round].round(2)

    df.sort_index(ascending=False, inplace=True)
    st.dataframe(df)

if __name__ == '__main__':
    loadData(start_date=st.session_state['start_date'], end_date=st.session_state['end_date'])
