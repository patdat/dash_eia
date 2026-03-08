import plotly.graph_objs as go
import numpy as np
import pandas as pd
from src.wps.mapping import production_mapping
from src.utils.colors import RED, BLUE, GREEN, BLACK, WHITE, MA_COLORS

def chart_trend(df, id, btn_1m, btn_3m, btn_12m, btn_36m, btn_60m,
                toggle_main_line=True,
                toggle_ma_1m=True, toggle_ma_3m=True, toggle_ma_12m=True):
    df = df.rename(columns={id: 'value'})
    last_value = df['value'].iloc[-1]

    mapping_name = production_mapping[id]
    mapping_name = mapping_name.replace('(kb)', '(mb)')
    mapping_name = mapping_name.replace('(kbd)', '(kb/d)')
    mapping_name = mapping_name.replace('(mbd)', '(mb/d)')

    stocks_in_name = 'stocks' in mapping_name.lower()
    if stocks_in_name:
        formatted_value = f"{round(last_value, 1):.1f}"
    else:
        formatted_value = f"{int(round(last_value, 0))}"

    # Compute moving averages BEFORE time-range filter
    df['ma_1m'] = df['value'].rolling(window=4, min_periods=1).mean()
    df['ma_3m'] = df['value'].rolling(window=13, min_periods=1).mean()
    df['ma_12m'] = df['value'].rolling(window=52, min_periods=1).mean()

    # Filter data based on the button selection
    if btn_1m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(months=1)]
    elif btn_3m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(months=3)]
    elif btn_12m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=1)]
    elif btn_36m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=3)]
    elif btn_60m:
        df = df[df['period'] >= df['period'].max() - pd.DateOffset(years=5)]

    period_as_array = np.array(df['period'])

    traces = []

    if toggle_main_line:
        traces.append(go.Scatter(
            x=period_as_array,
            y=df['value'],
            mode='lines',
            line=dict(color=BLACK),
            hoverinfo='text',
            hoverlabel=dict(bgcolor=RED, font=dict(color=WHITE)),
            text=[f"{d.strftime('%m/%d')}, {formatted_value}" for d in df['period']],
            showlegend=False,
        ))

    # Moving average traces
    ma_config = [
        (toggle_ma_1m, 'ma_1m', '1m MA', MA_COLORS[0]),
        (toggle_ma_3m, 'ma_3m', '3m MA', MA_COLORS[1]),
        (toggle_ma_12m, 'ma_12m', '12m MA', MA_COLORS[2]),
    ]
    any_ma_active = False
    for toggle, col, name, color in ma_config:
        if toggle:
            any_ma_active = True
            traces.append(go.Scatter(
                x=period_as_array,
                y=df[col],
                mode='lines',
                line=dict(color=color, width=1.5),
                hoverinfo='skip',
                name=name,
                showlegend=True,
            ))

    layout = go.Layout(
        title=dict(
            text=mapping_name,
            y=0.95,
            x=0.05,
            xanchor='left',
            yanchor='top',
            font=dict(
                color=BLACK
            )
        ),
        height=600,
        plot_bgcolor=WHITE,
        showlegend=any_ma_active,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date',
            showline=True,
            linecolor=BLACK,
            gridcolor=WHITE,
            spikedash='dot',
            spikecolor=GREEN,
            spikethickness=1,
            showspikes=True
        ),
        yaxis=dict(
            showline=True,
            linecolor=BLACK,
            gridcolor=WHITE,
            spikedash='dot',
            spikecolor=GREEN,
            spikethickness=1,
            showspikes=True,
            automargin=True,
            autorange=True
        ),
        shapes=[
            dict(
                type='line',
                x0=df['period'].min(),
                y0=last_value,
                x1=df['period'].max(),
                y1=last_value,
                line=dict(color=GREEN, width=1, dash='dot'),
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
                bgcolor=GREEN,
                font=dict(color=WHITE),
                xanchor='right'
            )
        ],
        margin=dict(l=40, r=40, t=75, b=25),
    )

    return {'data': traces, 'layout': layout}
