#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chart_data.py

Functions to organize data into charts from which we can compare
our devices.

Created on Mon Apr 10 17:25:39 2017

@author: jon.clucas
"""
from config import devices, organized_dir, placement_dir
from datetime import datetime
from organize_wearable_data import datetimedt, datetimeint
import json, numpy as np, os, pandas as pd, matplotlib.pyplot as plt

with open(os.path.join('./line_charts/device_colors.json')) as fp:
    color_key = json.load(fp)
facecolors = {}
facecolors['left'] = 'lightblue'
facecolors['right'] = 'red'

def main():
    people_df = getpeople()
    people_w = pd.unique(people_df.person_wrist)
    for pw in people_w:
        buildperson(people_df, pw)
    
def buildperson(df, pw):
    """
    Function to build plottable csv file for each available person-wrist-device
    
    Paramters
    ---------
    df : pandas dataframe
        dataframe with columns ["person_wrist", "device", "start", "stop"]
        detailing which device was worn by whom when
        
    pw : 2-tuple (person_name : string, wrist : string)
        indentifier for csv to build
        
    Returns
    -------
    None
    
    Outputs
    -------
    person_wrist.csv : csv file
        csv file formatted for plotting
    """
    person, start, stop = get_startstop(df, pw)
    person_df = df.loc[df['person_wrist'] == pw].copy()
    person_df.reset_index(drop=True, inplace=True)
    devices = pd.unique(person_df.device)
    print(person, end=": ")
    print(devices)
    csv_df = pd.DataFrame(columns=['device', 'Timestamp', 'x', 'y', 'z'])
    for device in devices:
        acc_path = os.path.join(organized_dir, 'accelerometer', '.'.join([
                   device, 'csv']))
        if os.path.exists(acc_path):
            device_df = pd.read_csv(acc_path)
            device_df.sort_values(by='Timestamp', inplace=True)
            try:
                device_df[['Timestamp']] = device_df.Timestamp.map(lambda x:
                                       datetimeint(str(x)))
            except:
                pass
            person_device_df = device_df.loc[(device_df['Timestamp'] >= start)
                               & (device_df['Timestamp'] <= stop)].copy()
            del device_df
            # write_csv(person_device_df, person, 'accelerometer', device)
            person_device_df[['Timestamp']] = person_device_df.Timestamp.map(
                                              lambda x: datetimedt(x))
            print(device, end=" ranges: x=(")
            print(min(person_device_df.x), end=", ")
            print(max(person_device_df.x), end="), y=(")
            print(min(person_device_df.y), end=", ")
            print(max(person_device_df.y), end="), z=(")
            print(min(person_device_df.z), end=", ")
            print(max(person_device_df.z), end=")\n")
            person_device_df['device'] = device
            person_device_df = person_device_df[['device', "Timestamp", "x",
                               "y", "z"]]
            csv_df = pd.concat([csv_df, person_device_df])
    if len(csv_df) > 0:
        csv_df = split_datetimes(csv_df)
        csv_df.sort_values(by=["Datestamp", "Timestamp"], inplace=True)
        for d in csv_df.Datestamp.unique():
            df_to_csv = csv_df.loc[(csv_df['Datestamp'] == d)]
            person_df_to_csv = df_to_csv.pivot(index="Timestamp", columns=
                               "device")
            person_df_to_csv.sortlevel(inplace=True)
            del person_df_to_csv['Datestamp']
            linechart(person_df_to_csv, pw, d)
            # write_csv(person_df_to_csv, person, 'accelerometer', d)
        
def linechart(df, pw, d=None):
    """
    Function to build a linechart of the given (person, wrist) and export an
    SVG of the image.
    
    Parameters
    ----------
    df : pandas dataframe
        dataframe to plot
    
    pw : 2-tuple (person_name : string, wrist : string)
        identifiers for plot
        
    d : date or None
        date
        
    Returns
    -------
    None
    
    Outputs
    -------
    person_wrist.svg : svg file
        svg of lineplot
    """
    sensors = ['accelerometer']
    for sensor in sensors:
        print("Plotting...")
        print(pw, end=" ")
        if d:
            print(d, end=" ")
            svg_out = os.path.join(organized_dir, sensor, "_".join([
                      d.isoformat(), pw[0], '.'.join([pw[1], 'svg'])]))
        else:
            svg_out = os.path.join(organized_dir, sensor, "_".join([pw[0], 
                  '.'.join([pw[1], 'svg'])]))   
        fig, axes = plt.subplots(figsize=(10, 8), dpi=75, nrows=3, ncols=1,
                    sharex=True)
        i = 0
        for axis in ['x', 'y', 'z']:
            plot_df = df.xs(axis, level=0, axis=1)
            for device in list(plot_df.columns):
                plot_line = plot_df[[device]].dropna()
                if "GENEActiv" in device:
                    label = "GENEActiv"
                else:
                    label = device
                axes[i].plot_date(x=plot_line.index, y=plot_line, color=
                        color_key[device], alpha=0.5, label=label, marker="",
                        linestyle="solid")
            if i == 0:
                axes[i].legend(loc='best', fancybox=True, framealpha=0.5)
            i = i + 1
        if d:
            plt.suptitle(''.join([d.isoformat(), ' ', pw[0], ', ', pw[1],
                         ' wrist']))
        else:
            plt.suptitle(''.join([pw[0], ', ', pw[1], ' wrist']))
        plt.xticks(rotation=65)
        print("".join(["Saving ", svg_out]))
        fig.savefig(svg_out, facecolor=facecolors[pw[1]])
        print("Saved.")
        plt.close()
        
def getpeople():
    """
    Function to organize timestamps by people and wrists.
    
    Parameters
    ----------
    None

    Returns
    -------
    people_df : pandas dataframe
        dataframe with columns ["person_wrist", "device", "start", "stop"]
        detailing which device was worn by whom when
    """
    # location = pd.read_csv(os.path.join(placement_dir, 'location.csv'))
    person = pd.read_csv(os.path.join(placement_dir, 'person.csv'))
    wrist = pd.read_csv(os.path.join(placement_dir, 'wrist.csv'))
    person_wrist = pd.DataFrame()
    pw0 = pd.merge(person, wrist, how="outer", on="﻿Timestamp", suffixes=(
          '_person', '_wrist'))
    person_wrist[['Timestamp']] = pw0[["﻿Timestamp"]]
    person_wrist['Actigraph'] = tuple(zip(pw0.Actigraph_person,
                                pw0.Actigraph_wrist))
    person_wrist['E4'] = tuple(zip(pw0.E4_person, pw0.E4_wrist))
    person_wrist['Embrace'] = tuple(zip(pw0.Embrace_person, pw0.Embrace_wrist))
    person_wrist['GENEActiv_black'] = tuple(zip(pw0.ix[:,
                                      'GeneActiv (black)_person'], pw0.ix[:,
                                      'GeneActiv (black)_wrist']))
    person_wrist['GENEActiv_pink'] = tuple(zip(pw0.ix[:,
                                      'GeneActiv (pink)_person'], pw0.ix[:,
                                      'GeneActiv (pink)_wrist']))
    person_wrist['Wavelet'] = tuple(zip(pw0.Biostrap_person, pw0.Biostrap_wrist
                              ))
    del pw0
    chart_wrists = []
    times = []
    for v in list(pd.unique(person_wrist.values.ravel())):
        if(type(v)) == tuple and v != (np.nan, np.nan):
            chart_wrists.append(v)
        elif(type(v) == int):
            times.append(v)
    chart_wrists.sort()
    times.sort()
    start_stop = {}
    for i, t in enumerate(times):
        if i < len(times) - 1:
            start_stop[t] = times[i + 1]
    people = []
    for pw in chart_wrists:
        for device in devices:
            for i, item in enumerate(person_wrist.ix[:, device]):
                if item == pw:
                    people.append([pw, device, person_wrist.loc[i, 'Timestamp'
                                  ],  start_stop[person_wrist.loc[i,
                                  'Timestamp']]])
    people_df = pd.DataFrame(people, columns=["person_wrist", "device",
                "start", "stop"])
    people_df[['start']] = people_df.start.map(lambda x:
                           datetime.fromtimestamp(int(x)))
    people_df[['stop']] = people_df.stop.map(lambda x:
                          datetime.fromtimestamp(int(x)))
    return(people_df)
    
def get_startstop(df, person):
    """
    Function to get overall start and stop times for each person-wrist.
    
    Parameters
    ----------
    df : pandas dataframe
        dataframe of at least ["person_wrist", "start", "stop"]
        
    person : string
        person-wrist to get start and stop for

    Returns
    -------
    person_start_stop : 3-tuple (string, datetime, datetime)
        person-wrist, overall start time, overall stop time (times in Linux
        time format)
    """
    starts = []
    stops = []
    for i, item in enumerate(df.person_wrist):
        if item == person:
            starts.append(df.loc[i, 'start'])
            stops.append(df.loc[i, 'stop'])
    ssdt = "%Y-%m-%d %H:%M:%S"
    return(person, datetimeint(min(starts).strftime(ssdt), ssdt),
           datetimeint(max(stops).strftime(ssdt), ssdt))
    
def split_datetimes(df):
    """
    Function to split datetimes into dates and times.
    
    Parameters
    ----------
    df : pandas dataframe
        dataframe with "Timestamp" column
        
    Returns
    -------
    dtdf : pandas dataframe
        dataframe with "Datestamp" and "Timestamp" columns
    """
    dtdf = df.copy()
    try:
        dtdf['Datestamp'] = dtdf.Timestamp.map(lambda x: x.to_datetime().date()
                            )
    except:
        dtdf['Datestamp'] = dtdf.Timestamp.map(lambda x: x.date())
    return(dtdf)

def write_csv(df, person, sensor, device=None, d=None):
    """
    Function to write a csv for a person-wrist for a particular sensor.
    
    Parameters
    ----------
    df : pandas dataframe
        dataframe to write to csv
        
    person : 2-tuple (string, string)
        person_name, wrist
        
    sensor : string
        type of sensor data included in df
    
    device : string or None
        device name
        
    d : datetime.date or None
        date  
    
    Returns
    -------
    df : pandas dataframe
        unchanged dataframe
        
    Output
    ------
    csv : csv file
        csv copy of dataframe stored in
        organized_dir/`sensor`/`person_name`_`wrist`_`sensor`.csv
    """
    if device:
        if d:
            csv_out = os.path.join(organized_dir, sensor, "_".join([
                      d.isoformat(), person[0], person[1], '.'.join([device,
                      'csv'])]))
        else:
            csv_out = os.path.join(organized_dir, sensor, "_".join([person[0],
                      person[1], '.'.join([device, 'csv'])]))
    else:
        if d:
            csv_out = os.path.join(organized_dir, sensor, "_".join([
                      d.isoformat(), person[0], '.'.join([person[1], 'csv'])]))
        else:
            csv_out = os.path.join(organized_dir, sensor, "_".join([person[0],
                      '.'.join([person[1], 'csv'])]))
    if not os.path.exists(os.path.dirname(csv_out)):
        os.makedirs(os.path.dirname(csv_out))
    print(''.join(["Saving ", csv_out]))
    df.to_csv(csv_out, index=False)
    return(df)

# ============================================================================
if __name__ == '__main__':
    main()