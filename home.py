import streamlit as st
import ee
import json
from datetime import date
import geemap.foliumap as geemap

st.set_page_config(
    page_title='Sentinel 2 Project',
    layout='wide'
)

json_data = st.secrets['json_data']
service_account = st.secrets['service_account']

@st.cache_data
def Initialize():
    json_object = json.loads(json_data, strict=False)
    json_object = json.dumps(json_object)

    credentials = ee.ServiceAccountCredentials(service_account,key_data=json_object)
    ee.Initialize(credentials)

if __name__ == '__main__':
    Initialize()


# st.markdown("<h1 style='text-align: center; color: black;'>Sentinel 2 Maps</h1>", unsafe_allow_html=True)

col1,col2 = st.columns([1,3])
with col1:
    basemapsList = ['ROADMAP', 'SATELLITE']
    st.selectbox('Pilih Basemap', options=basemapsList, key='basemap', index=0)
    with st.expander('Mencari citra berdasarkan koordinat',expanded=True):
        with st.form('my_form'):
            st.text_input('Masukkan Latitude', value=-6.737246, key='latitude')
            st.text_input('Masukkan Longitude', value=108.550659, key='longitude')
            submit = st.form_submit_button('Submit')

    def load_dataset(latitude, longitude, cloudmask):
        s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
        QA_BAND = csPlus.first().bandNames()

        def mask(image):
            CLEAR_THRESHOLD = 0.60
            return image.updateMask(image.select('cs').gte(CLEAR_THRESHOLD))
        
        def scaling(image):
            opticalBands = image.select('B.*').divide(10000)
            return image.addBands(opticalBands, None, True)
        
        def addNDVI(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
            return image.addBands(ndvi)

        def addNDWI(image):
            ndwi = image.normalizedDifference(['B3', 'B11']).rename('NDWI')
            return image.addBands(ndwi)
        
        def addNDBI(image):
            ndbi = image.expression('(SWIR1 - NIR) / (SWIR1 + NIR)', {
                'SWIR1': image.select('B11'), 
                'NIR': image.select('B8'), 
                'BLUE': image.select('B2')}).rename('NDBI')
            return image.addBands(ndbi)
        
        def addEVI(image):
            evi = image.expression('2.5 * (NIR - RED) / ((NIR + 6*RED - 7.5*BLUE) + 1)', {
                'NIR': image.select('B8'),
                'RED': image.select('B4'),
                'BLUE': image.select('B2')}).rename('EVI')
            return image.addBands(evi)
        
        def addSAVI(image):
            savi = image.expression('((NIR-RED)/(NIR+RED+0.5))*1.5', {
                'NIR': image.select('B8'),
                'RED': image.select('B4')}).rename('SAVI')
            return image.addBands(savi)
        
        def addBSI(image):
            bsi = image.expression('((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2))', {
                'B11': image.select('B11'),
                'B4': image.select('B4'),
                'B8': image.select('B8'),
                'B2': image.select('B2')}).rename('BSI')
            return image.addBands(bsi)
        
        site = ee.Geometry.Point([longitude,latitude])

        if cloudmask:
            dataset = (s2.filterBounds(site)
                        .filterDate('2017-01-01', str(date.today()))
                        .linkCollection(csPlus, QA_BAND)
                        .map(mask)
                        .map(scaling)
                        .map(addNDVI)
                        .map(addNDWI)
                        .map(addNDBI)
                        .map(addEVI)
                        .map(addSAVI)
                        .map(addBSI)

            )
        else:
            dataset = (s2.filterBounds(site)
                        .filterDate('2017-01-01', str(date.today()))
                        .linkCollection(csPlus, QA_BAND)
                        .map(scaling)
                        .map(addNDVI)
                        .map(addNDWI)
                        .map(addNDBI)
                        .map(addEVI)
                        .map(addSAVI)
                        .map(addBSI)                       
            
            )

        return dataset
            
if 'pass' not in st.session_state:
    st.session_state['pass'] = False

if submit or st.session_state['pass']:
    st.session_state['pass'] = True
    latitude = float(st.session_state.latitude)
    longitude = float(st.session_state.longitude)
    with col1:
        with st.expander('Opsi Scene'):
            mask_container = st.container()
            masking = st.checkbox('Cloud Masking')

            if masking:
                st.session_state['mask'] = True
                dataset = load_dataset(latitude, longitude, True)
                scene_list = dataset.aggregate_array('system:index').getInfo()
                mask_container.selectbox('Pilih Scene', options=scene_list, key='scene_id')

            else:
                st.session_state['mask'] = False
                dataset = load_dataset(latitude, longitude, False)
                scene_list = dataset.aggregate_array('system:index').getInfo()
                mask_container.selectbox('Pilih Scene', options=scene_list, key='scene_id')     

        with st.expander('Opsi Layer'):
            st.markdown(' ')
            composite_container = st.container()
            composite_all = st.checkbox('All Composite')
            composite_options = ['True Color','False Color','Color Infrared']

            if composite_all:
                composite_container.multiselect(
                    label = 'Band Composite',
                    options = composite_options,
                    default = composite_options,
                    key = 'band_composite'
                )
            else:
                composite_container.multiselect(
                    label='Band Composite',
                    options= composite_options,
                    key='band_composite'
                )
    
        bandlist_container = st.container()
        bandlist_all = st.checkbox('All Bands')
        bandlist_options = [
                            'B1','B2','B3','B4',
                            'B5','B6','B7','B8',
                            'B8A','B9','B11','B12',
                            'NDVI','NDWI','NDBI',
                            'EVI','SAVI','BSI'
                            ]

        if bandlist_all:
            bandlist_container.multiselect(
                label = 'List of bands', 
                options = bandlist_options, 
                default = bandlist_options, 
                key = 'band_list')
        else:
            bandlist_container.multiselect(
                label = 'List of bands', 
                options = bandlist_options, 
                key = 'band_list')

        composite = st.session_state['band_composite']
        bands = []

        for item in composite:
            if item == 'True Color':
                bands.append({'True Color':['B4','B3','B2']})
            elif item == 'False Color':
                bands.append({'False Color':['B11','B8','B3']})
            elif item == 'Color Infrared':
                bands.append({'Color Infrared':['B8','B4','B3']})


        ratio = st.session_state['band_list']
        band_list = []
        for item in ratio:
            if item == 'B1':
                band_list.append('B1')
            elif item == 'B2':
                band_list.append('B2')
            elif item == 'B3':
                band_list.append('B3')
            elif item == 'B4':
                band_list.append('B4')
            elif item == 'B5':
                band_list.append('B5')
            elif item == 'B6':
                band_list.append('B6')
            elif item == 'B7':
                band_list.append('B7')
            elif item == 'B8':
                band_list.append('B8')
            elif item == 'B8A':
                band_list.append('B8A')
            elif item == 'B9':
                band_list.append('B9')
            elif item == 'B11':
                band_list.append('B11')
            elif item == 'B12':
                band_list.append('B12')
            elif item == 'NDVI':
                band_list.append('NDVI')
            elif item == 'NDWI':
                band_list.append('NDWI')
            elif item == 'NDBI':
                band_list.append('NDBI')
            elif item == 'EVI':
                band_list.append('EVI')
            elif item == 'SAVI':
                band_list.append('SAVI')
            elif item == 'BSI':
                band_list.append('BSI')



    Map = geemap.Map(

        add_google_map=False,
        plugin_Draw=False,
        search_control=False,
        plugin_LatLngPopup=True
        )

    basemap = st.session_state['basemap']
    scene = st.session_state['scene_id']

    @st.cache_data
    def layer(latitude, longitude, basemap, scene, bands, cloudmask, band_list):

        data = load_dataset(latitude, longitude, cloudmask).filter(ee.Filter.eq('system:index', scene)) \
                    .first()

        popup = f'Latitude: {latitude}\nLongitude: {longitude}'
        Map.add_basemap(basemap=basemap)
        Map.add_marker(location=[latitude, longitude], tooltip=popup)

        for dict in bands:
            for key,value in dict.items():
                if key in ['False Color','Color Infrared']:
                    Map.addLayer(data, {'min':0,'max':0.35,'bands':value}, key, True)
                
                else:
                    Map.addLayer(data, {'min':0,'max':0.3,'bands':value}, key, True)

        for item in band_list:
            if item == 'B1':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B2':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B3':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B4':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B5':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B6':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B7':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B8':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B8A':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B9':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B11':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'B12':
                Map.addLayer(data, {'min':0,'max':0.3,'bands':item}, item, True)
            elif item == 'NDVI':
                Map.addLayer(data, {'min':0,'max':1,'bands':item, 'palette':['#640000','#ff0000','#ffff00','#00c800','#006400']}, item, True)
            elif item == 'NDWI':
                Map.addLayer(data, {'bands':item, 'palette':['red', 'yellow', 'green', 'cyan', 'blue']}, item, True)
            elif item == 'NDBI':
                Map.addLayer(data, {'min':-0.3, 'max':0.2,'bands':item, 'palette':['yellow', 'red']}, item, True)
            elif item == 'EVI':
                Map.addLayer(data, {'min':0,'max':1,'bands':item, 'palette':[
                                    'ffffff', 'ce7e45', 'df923d', 'f1b555', 'fcd163', '99b718', '74a901',
                                    '66a000', '529400', '3e8601', '207401', '056201', '004c00', '023b01',
                                    '012e01', '011d01', '011301']}, item, True)
            elif item == 'SAVI':
                Map.addLayer(data, {'min':0, 'max':0.58, 'bands':item, 'palette':["#b62f02","#d99208","#fcf40d","#36e014","#0a5c1c"]}, item, True)
            elif item == 'BSI':
                Map.addLayer(data, {'min':0, 'max':1,'bands':item, 'palette':['#ffffcc','#ffeda0','#fed976','#feb24c','#fd8d3c','#fc4e2a','#e31a1c','#bd0026','#800026']}, item, True)
              


        Map.centerObject(ee.Geometry.Point([longitude, latitude]), zoom=11)
        Map.to_streamlit(height=480)

    with col2:
        layer(

            latitude=latitude,
            longitude=longitude,
            basemap=basemap,
            scene=st.session_state.scene_id,
            bands=bands,
            cloudmask=st.session_state.mask,
            band_list=band_list

        )

else:
    with col2:
        Map = geemap.Map(
            add_google_map=False,
            plugin_Draw=False,
            search_control=False,
            plugin_LatLngPopup=True,
            basemap=st.session_state['basemap']
            )

        Map.to_streamlit(height=480)

st.write(st.session_state)