from src.wps.mapping import production_mapping
import plotly.graph_objects as go

from src.utils.variables import range_selector_normal, range_selector_last_five_years, year_1_string, year_2_string, year_3_string

tickvals = [0, 5, 9, 14, 18, 22, 27, 31, 36, 40, 45, 49]
ticktext = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def chart_seasonality(df, id, toggle_seag_range, toggle_year_1,toggle_year_2,toggle_year_3):

    def format_value(val, column_name):
        if "stocks" in column_name.lower():
            return f"{val:,.1f}" if val >= 0 else f"({abs(val):,.1f})"
        else:
            return f"{val:,.0f}" if val >= 0 else f"({abs(val):,.0f})"


    mapping_name = production_mapping[id]
    if 'stocks' in mapping_name.lower():
        mapping_name = mapping_name.replace('(kbd)', '(kb/d)')
        mapping_name = mapping_name.replace('(mbd)', '(mb/d)')        
        mapping_name = mapping_name.replace('(kb)', '(mb)')

    df = df[df['id']==id]

    if not toggle_seag_range:
        min_rng = df[f'min_{range_selector_normal}']
        max_rng = df[f'max_{range_selector_normal}']
        avg_rng = df[f'average_{range_selector_normal}']
    else:
        min_rng = df[f'min_{range_selector_last_five_years}']
        max_rng = df[f'max_{range_selector_last_five_years}']
        avg_rng = df[f'average_{range_selector_last_five_years}']    


    traces = []

    traces.append(go.Scatter(
        x=df['week_of_year'],
        y=min_rng,
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))

    traces.append(go.Scatter(
        x=df['week_of_year'],
        y=max_rng,
        mode='lines',
        fill='tonexty',
        fillcolor='#f4f5f9',
        line_color='#f4f5f9', 
        showlegend=False,
        hoverinfo='skip'
    ))

    traces.append(go.Scatter(
        x=df['week_of_year'],
        y=avg_rng,
        mode='lines',
        line=dict(color='black', dash='dot', width=1),
        showlegend=False,
        hoverinfo='skip'
    ))

    if not toggle_year_3:
        traces.append(go.Scatter(
            x=df['week_of_year'],
            y=df[f'actual_{year_3_string}'],
            mode='lines',
            name=year_3_string,
            hoverinfo='text',
            text=[f"{date}: {format_value(value, mapping_name)}" for date, value in zip(df[f'dates_actual_{year_3_string}'], df[f'actual_{year_3_string}'])],
            line=dict(color='#c00000', dash='solid', width=2),
        ))

    if not toggle_year_2:
        traces.append(go.Scatter(
            x=df['week_of_year'],
            y=df[f'actual_{year_2_string}'],
            mode='lines',
            name=year_2_string,
            hoverinfo='text',
            line=dict(color='#e97132', dash='solid', width=2),
            text=[f"{date}: {format_value(value, mapping_name)}" for date, value in zip(df[f'dates_actual_{year_2_string}'], df[f'actual_{year_2_string}'])],
        ))

    if not toggle_year_1:
        traces.append(go.Scatter(
            x=df['week_of_year'],
            y=df[f'actual_{year_1_string}'],
            mode='lines',
            name=year_1_string,
            hoverinfo='text',
            line=dict(color='#bfbec4', dash='solid', width=2),
            text=[f"{date}: {format_value(value, mapping_name)}" for date, value in zip(df[f'dates_actual_{year_1_string}'], df[f'actual_{year_1_string}'])],
        ))

    layout = go.Layout(

        title=dict(
            text=mapping_name,
            y=0.97,
            x=0.03,
            xanchor='left',
            yanchor='top',
            font=dict(
                color='black'
            )
        ),   
        height=600,
        xaxis=dict(
            range=[0, len(df['week_of_year']) - 1],
            tickmode='array',
            tickvals=tickvals,
            ticktext=ticktext,
            type='category',
            showspikes=True,
            spikedash='solid',
            spikecolor='grey',
            spikethickness=0.5,
            spikemode='across',
            showline=True,
            showgrid=False,
            linecolor='black',
            linewidth=0.5,
            zeroline=False
        ),
        yaxis=dict(
            tickformat=',.0fK',
            showgrid=False,
            showline=True,
            linecolor='black',
            linewidth=0.5,
            zeroline=False
        ),
        hovermode='x unified',
        template='plotly_white',
        legend=dict(
            x=0.85,
            y=1.0,
            xanchor='left',
            yanchor='top',
            orientation='v'
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Montserrat",
            bordercolor="#ccc"
        ),
        margin=dict(l=40, r=40, t=40, b=25),        
        showlegend=True
    )


    # Return the figure as a dictionary
    return {'data': traces, 'layout': layout}