import plotly.graph_objs as go

def chart_trend(df, mapping_name, stocks_in_name):
    df = df.copy()
    last_value = df['value'].iloc[-1]

    if stocks_in_name:
        formatted_value = f"{round(last_value, 1):.1f}"  # Ensure one decimal place is always shown
    else:
        formatted_value = f"{int(round(last_value, 0))}"  # Convert to integer to avoid decimal

    trace = go.Scatter(
        x=df['period'],
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
            rangeselector=dict(
                buttons=[
                    {'count': 1, 'label': '1m', 'step': 'month', 'stepmode': 'backward'},
                    {'count': 6, 'label': '6m', 'step': 'month', 'stepmode': 'backward'},
                    {'count': 12, 'label': '1y', 'step': 'month', 'stepmode': 'backward'},
                    {'count': 36, 'label': '3y', 'step': 'month', 'stepmode': 'backward'},
                    {'step': 'all'}
                ]
            ),
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
            showspikes=True
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