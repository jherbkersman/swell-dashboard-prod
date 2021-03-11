
#!/usr/bin/env python3

"""
Created on Mon Mar  1 21:06:43 2021

@author: jack
"""

# -*- coding: utf-8 -*-

# check on runtime
import time
start_time = time.time()

# import the modules needed to generate the deshboard
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

# import the web interface library and pandas for data manipulation
from urllib.request import urlopen
import pandas as pd

# import a module from scipy for maxima detection
from scipy.signal import find_peaks

# map the buoys to their locations
buoyLocations = {46059: 'San Fransisco',
                 46259: 'San Luis Obispo',
                 46219: 'South Channel Islands',
                 46086: 'San Diego',
                 46047: 'Cortes Bank'}

# set the columns to be used when reading the csv
colIndexD = [5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28,
            30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60,
            62, 64, 66, 68, 70, 72, 74, 76, 78, 80, 82, 84, 86, 88, 90, 92,
            94, 96]
colIndexA = [5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35,
            37, 39, 41, 43, 45, 47, 49, 51, 53, 55, 57, 59, 61, 63, 65,
            67, 69, 71, 73, 75, 77, 79, 81, 83, 85, 87, 89, 91, 93, 95]
    
# set the column names (quotes prevent interaction with colIndex numbers during read)   
colNames = ["Sep_Freq", "30.3", "26.32", "23.26",
            "20.83", "18.87", "17.24", "15.87", "14.71", "13.7", "12.82", "12.05", "11.36",
            "10.75", "10", "9.09", "8.33", "7.69", "7.14", "6.67", "6.25", "5.88", "5.56", "5.26",
            "5", "4.76", "4.55", "4.35", "4.17", "4", "3.85", "3.7", "3.57", "3.45", "3.33", "3.23",
            "3.13", "3.03", "2.94", "2.86", "2.74", "2.6", "2.47", "2.35", "2.25", "2.15", "2.06"]     

# define the possible integer seconds that the swells can fall under
discreteSecs = ["30", "26", "23", "21", "19", "17", "16", "15", "14", "13", "12",
                "11", "10", "9", "8", "7", "6", "5", "4", "3", "2"]

# define the mapping of which readings need to go where for the periods that
# have more than one reading in their bucket
discreteMap = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11, 12, 13, 14, 14, 15,
               15, 16, 16, 16, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 19, 19,
               19, 19, 19, 19, 19, 19, 19, 20, 20, 20, 20, 20]



# define a function to convert degree to cardinal direction
def degrees_to_cardinal(d):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = int((d + 11.25)/22.5 - 0.02)
    return dirs[ix % 16]

# definte the function to pull the buoy data and transform it
def dataWrangle(buoy):
    
    # get an HTTP response from the NDBC sources
    den = urlopen("http://www.ndbc.noaa.gov/data/realtime2/{}.data_spec".format(buoy))
    a1 = urlopen("https://www.ndbc.noaa.gov/data/realtime2/{}.swdir".format(buoy))
    
    print("Data Load Time:", round(time.time() - start_time, 2), "seconds")
    print()
    
    
    # read in the csv's
    tempNames = ['YYYY', 'MM', 'DD', 'HH', 'mm']
    for i in colNames:
        tempNames.append(i)
    tempCols = [0, 1, 2, 3, 4]
    tempCols.extend(colIndexD)
    density = pd.read_csv(den, delimiter=" ", skiprows=1, header=None, nrows=1,
                      usecols=tempCols, names=tempNames)
    alpha1 = pd.read_csv(a1, delimiter=" ", skiprows=1, header=None, nrows=1,
                      usecols=colIndexA, names=colNames[1:])
    
    # get the time data from the csv and drop it
    updateTime = density.iloc[0,:5]
    density.drop(labels = ['YYYY', 'MM', 'DD', 'HH', 'mm'], axis = 1)
    
    # convert the separation frequency from hZ to seconds
    density.iloc[0,0] = round(1 / density.iloc[0,0], 3)
    
    # take the max value for the periods that have more than one reading
    discMaxEnergy = []
    discDirection = []
    discCardinal = []
    prevJ = 0
    for i, j, k in zip(density.iloc[0,1:], discreteMap, alpha1.iloc[0,]):
        if len(discMaxEnergy) == 0:
            discMaxEnergy.append(round(i,3))
            discDirection.append(int(k))
            discCardinal.append(degrees_to_cardinal(k))
        elif prevJ == j:
            if discMaxEnergy[-1] < i:
                discMaxEnergy[-1] = round(i,3)
                discDirection[-1] = int(k)
                discCardinal[-1] = degrees_to_cardinal(k)
        else:
            discMaxEnergy.append(round(i,3))
            discDirection.append(int(k))
            discCardinal.append(degrees_to_cardinal(k))
            prevJ = j
          
    # create a dataframe out of the data
    discreteData = pd.DataFrame([discMaxEnergy, discDirection, discCardinal],
                                columns=discreteSecs,
                                index=(["Energy (m^2 / hZ)", "Mean Direction", "Cardinal Direction"]))
    
    print("Current Swell Info for Buoy", buoy)
    print()
    
    print(discreteData.iloc[0:3,6:15])
    print()
     
    
    # USE THE BELOW CODE TO WORK ONLY WITH 'DISRETE' DATA
    '''
    # find peaks of the frquency domain
    peaks = find_peaks(discreteData.iloc[0,])[0]
    
    r = []
    theta = []
    width = []
    for i in peaks:
        r.append(round(discreteData.iloc[0,i], 3))
        theta.append(discDirection[i])
        width.append(20 + (round(discreteData.iloc[0,i], 3) / 50))
    '''
    # find peaks of the frquency domain
    peaks = find_peaks(density.iloc[0,5:])[0]
    
    # prepare the data for the function to return
    r = []
    theta = []
    width = []
    info = []
    for i in peaks[:4]:
        r.append((density.iloc[0,i+5]))# ** (1./4.) * 1.5)
        theta.append(alpha1.iloc[0,i])
        width.append(35)
        info.append(str(int(round(float(density.columns[i+5]), 0))) + " sec. " + degrees_to_cardinal(alpha1.iloc[0,i]))    

    print()
    print("Total Runtime:", round(time.time() - start_time, 2), "seconds")
    
    return r, theta, width, updateTime, info




# During development:
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.




# define a function to translate between plotly theta coordinate system
# and the compass directional degrees (also one for lists)
def convertDeg(x):
    if x <= 90:
        return (90 - x)
    else:
        return (450 - x)
    
def convertListDeg(l):
    y = []
    for x in l:
        y.append(convertDeg(x))
    return y


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

# definte the buoy to be analyzed
buoy = 46219

# prepare data to be called
rData, thetaData, widthData, updateTime, infoData = dataWrangle(buoy)

# handle the update time
updateDay = '{}/{}'.format(int(updateTime[1]), int(updateTime[2]))
updateHour = int(updateTime[3])
if updateHour < 9:
    updateHour += 16
else:
    updateHour -= 8
updateMinute = str(int(updateTime[4])).zfill(2)
updateAMPM = "AM"
if updateHour == 12:
    updateAMPM = "PM"
elif updateHour > 12:
    updateAMPM = "PM"
    updateHour = updateHour - 12

print()
print("Last update from buoy: {}:{}{} PST".format(updateHour,updateMinute,updateAMPM))
print()
print()

fig = go.Figure(go.Barpolar(
    r = rData,
    theta = convertListDeg(thetaData),
    width = widthData,
    marker_color=["#E4FF87", '#709BFF', '#B6FFB4', '#FFAA70'],
    marker_line_color="black",
    marker_line_width=2,
    opacity=0.8,
    text = infoData,
    hovertemplate = "%{r} m^2 / hZ <br>@ %{text} <extra></extra>",
))

fig.update_layout(
    template=None,
    polar = dict(
        radialaxis = dict(range=[0, max(rData) * 1.25], showticklabels=False, ticks=''),
        angularaxis = dict(showticklabels=True, ticks='', tickmode='array',
                           tickvals=[90, 45, 0, 315, 270, 225, 180, 135],
                           ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
    )
)
app.layout = html.Div(children=[
    
    html.H1(id='title', children='{} Swells - Buoy {}'.format(buoyLocations[buoy], buoy)),

    html.Div(id='subtitle', children='''
        Last update from buoy: {}:{} {} PST on {}
    '''.format(updateHour,updateMinute,updateAMPM,updateDay)),
    
    html.Div(children =[
        
        html.Div( children = [

            html.H6('Buoy Selection:'),
            dcc.RadioItems(
                id='buoySelection',
                options=[
                    {'label': 'San Fransisco', 'value': 46059},
                    {'label': 'San Luis Obispo', 'value': 46259},
                    {'label': 'South Channel Islands', 'value': 46219},
                    {'label': 'San Diego', 'value': 46086},
                    {'label': 'Cortes Bank', 'value': 46047}
                ],
                value=46219,
                
            ),
            
            
        ],
        style={'width': '15%', 'display': 'inline-block', 'justifyContent': 'center', 'text-align': 'justify', 'vertical-align': '40vh'}),
    
        dcc.Graph(
            id='swell-breakdown',
            figure=fig,
            style={'width': '80vh', 'height': '80vh', 'margin': 'auto', 'display': 'inline-block', 'color': 'grey'}
        )
    
    ]),
    
    
    html.Div(children='''
        A Plot by Jack Herbkersman
    ''', style={'font-style': 'italic'})

    
], style = {'textAlign': 'center'})

             
             
             
@app.callback(
    Output(component_id='title', component_property='children'),
    Output(component_id='subtitle', component_property='children'),
    Output(component_id='swell-breakdown', component_property='figure'),
    Input(component_id='buoySelection', component_property='value')
)
def update_output_div(input_value):
    
    # reload the buoy data from the NDBC
    rData, thetaData, widthData, updateTime, infoData = dataWrangle(input_value)
    # handle the update time
    updateHour = int(updateTime[3])
    if updateHour < 9:
        updateHour += 16
    else:
        updateHour -= 8
    updateMinute = str(int(updateTime[4])).zfill(2)
    updateAMPM = "AM"
    if updateHour == 12:
        updateAMPM = "PM"
    elif updateHour > 12:
        updateAMPM = "PM"
        updateHour = updateHour - 12
        
        
        
    fig = go.Figure(go.Barpolar(
        r = rData,
        theta = convertListDeg(thetaData),
        width = widthData,
        marker_color=["#E4FF87", '#709BFF', '#B6FFB4', '#FFAA70'],
        marker_line_color="black",
        marker_line_width=2,
        opacity=0.8,
        text = infoData,
        hovertemplate = "%{r} m^2 / hZ <br>@ %{text} <extra></extra>",
    ))
    fig.update_layout(
        template=None,
        polar = dict(
            radialaxis = dict(range=[0, max(rData) * 1.25], showticklabels=False, ticks=''),
            angularaxis = dict(showticklabels=True, ticks='', tickmode='array',
                               tickvals=[90, 45, 0, 315, 270, 225, 180, 135],
                               ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        )
    )
    
    return html.H1(id='title', children='{} Swells - Buoy {}'.format(buoyLocations[input_value], input_value)), html.Div(id='time', children='''Last update from buoy: {}:{} {} PST on {}'''.format(updateHour,updateMinute,updateAMPM,updateDay)), fig
             


if __name__ == '__main__':
    app.run_server(debug=True)
