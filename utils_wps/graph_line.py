import plotly.graph_objs as go
import numpy as np
import pandas as pd
from utils_wps.mapping import production_mapping

def chart_trend(df, id, btn_1m, btn_6m, btn_12m, btn_36m, btn_all):
    df = df.rename(columns={id: 'value'})
    last_value = df['value'].iloc[-1]
    
    mapping_name = production_mapping[id]
    mapping_name = mapping_name.replace('(kb)', '(mb)')        
    mapping_name = mapping_name.replace('(kbd)', '(kb/d)')
    mapping_name = mapping_name.replace('(mbd)', '(mb/d)')                
    
    stocks_in_name = 'stocks' in mapping_name.lower()
    if stocks_in_name:
        formatted_value = f"{round(last_value, 1):.1f}"  # Ensure one decimal place is always shown
    else:
        formatted_value = f"{int(round(last_value, 0))}"  # Convert to integer to avoid decimal

    # Filter data based on the button selection
    if btn_1m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(months=1)]
    elif btn_6m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(months=6)]
    elif btn_12m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=1)]
    elif btn_36m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=3)]
    elif btn_all:
        pass

    period_as_array = np.array(df['period'])  # Explicit conversion to numpy array

    trace = go.Scatter(
        x=period_as_array,
        y=df['value'],
        mode='lines',
        line=dict(color='#c00000'),
        hoverinfo='text',
        hoverlabel=dict(bgcolor='#e97132', font=dict(color='white')),
        text=[f"{d.strftime('%m/%d')}, {formatted_value}" for d in df['period']]  # List comprehension to format each hover text
    )

    layout = go.Layout(
        title=dict(
            text=mapping_name,
            y=0.95,
            x=0.05,
            xanchor='left',
            yanchor='top',
            font=dict(
                color='black'
            )
        ),
        plot_bgcolor='white',
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date',
            showline=True,
            linecolor='black',
            gridcolor='white',
            spikedash='dot',
            spikecolor='#e97132',
            spikethickness=1,
            showspikes=True
        ),
        yaxis=dict(
            showline=True,
            linecolor='black',
            gridcolor='white',
            spikedash='dot',
            spikecolor='#e97132',
            spikethickness=1,
            showspikes=True,
            automargin=True,
            autorange=True  # Automatically scale y-axis based on data values
        ),
        shapes=[
            dict(
                type='line',
                x0=df['period'].min(),
                y0=last_value,
                x1=df['period'].max(),
                y1=last_value,
                line=dict(color='#e97132', width=1, dash='dot'),
                xref='x',
                yref='y'
            )
        ],
        annotations=[
            dict(
                xref='paper',
                yref='y',
                x=0,
                y=last_value,
                text=formatted_value,
                showarrow=False,
                bgcolor='#e97132',
                font=dict(color='white'),
                xanchor='right'
            )
        ],
        margin=dict(l=40, r=40, t=75, b=25),        
    )

    # Return the figure as a dictionary
    return {'data': [trace], 'layout': layout}
