from utils.mapping import production_mapping
import plotly.graph_objects as go


tickvals = [0, 5, 9, 14, 18, 22, 27, 31, 36, 40, 45, 49]
ticktext = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def chart_seasonality(df, id, toggle_seag_range, toggle_2022,toggle_2023,toggle_2024):

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
        min_rng = df['min_1519']
        max_rng = df['max_1519']
        avg_rng = df['average_1519']
    else:
        min_rng = df['min_1823']
        max_rng = df['max_1823']
        avg_rng = df['average_1823']    


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

    if not toggle_2024:
        traces.append(go.Scatter(
            x=df['week_of_year'],
            y=df['actual_2024'],
            mode='lines',
            name='2024',
            hoverinfo='text',
            text=[f"{date}: {format_value(value, mapping_name)}" for date, value in zip(df['dates_actual_2024'], df['actual_2024'])],
            line=dict(color='#c00000', dash='solid', width=2),
        ))

    if not toggle_2023:
        traces.append(go.Scatter(
            x=df['week_of_year'],
            y=df['actual_2023'],
            mode='lines',
            name='2023',
            hoverinfo='text',
            line=dict(color='#e97132', dash='solid', width=2),
            text=[f"{date}: {format_value(value, mapping_name)}" for date, value in zip(df['dates_actual_2023'], df['actual_2023'])],
        ))

    if not toggle_2022:
        traces.append(go.Scatter(
            x=df['week_of_year'],
            y=df['actual_2022'],
            mode='lines',
            name='2022',
            hoverinfo='text',
            line=dict(color='#bfbec4', dash='solid', width=2),
            text=[f"{date}: {format_value(value, mapping_name)}" for date, value in zip(df['dates_actual_2022'], df['actual_2022'])],
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
            font_family="Open Sans",
            bordercolor="#ccc"
        ),
        margin=dict(l=40, r=40, t=40, b=25),        
        showlegend=True
    )


    # Return the figure as a dictionary
    return {'data': traces, 'layout': layout}




















# import pandas as pd
# import plotly.graph_objects as go

# def generate_seasonality_table(df):
#     df = df.copy()
    
#     def create_year(df,year):
#         df = df.copy()
#         df = df[df['period'].dt.year == year]
#         df['week_of_year'] = df['period'].dt.isocalendar().week
#         df.columns = [str(col) + '_' + str(year) for col in df.columns]    
#         df.columns = [col.replace(f'week_of_year_{year}','week_of_year') for col in df.columns]
#         return df

#     df_2015 = create_year(df,2015)
#     df_2016 = create_year(df,2016)
#     df_2017 = create_year(df,2017)
#     df_2018 = create_year(df,2018)
#     df_2019 = create_year(df,2019)
#     df_2020 = create_year(df,2020)
#     df_2021 = create_year(df,2021)
#     df_2022 = create_year(df,2022)
#     df_2021 = create_year(df,2021)
#     df_2022 = create_year(df,2022)
#     df_2023 = create_year(df,2023)
#     df_2024 = create_year(df,2024)

#     dfs = [df_2015,df_2016,df_2017,df_2018,df_2019,df_2020,df_2021,df_2022,df_2023,df_2024]

#     dff = dfs[0]
    
#     for df in dfs[1:]:
#         dff = pd.merge(dff, df, on='week_of_year', how='outer', suffixes=(False, False))
#     week_of_year = dff.pop('week_of_year')
#     dff.insert(0, 'week_of_year', week_of_year)      
    
#     dff = dff[dff['week_of_year'] <= 52]  
        
#     return dff

# def add_additional_seasonality_data(df):
#     df['avg_1519'] = df[['value_2015','value_2016','value_2017','value_2018','value_2019']].mean(axis=1)
#     df['avg_1823'] = df[['value_2018','value_2019','value_2021','value_2022','value_2023']].mean(axis=1)

#     df['min_1519'] = df[['value_2015','value_2016','value_2017','value_2018','value_2019']].min(axis=1)
#     df['min_1823'] = df[['value_2018','value_2019','value_2021','value_2022','value_2023']].min(axis=1)

#     df['max_1519'] = df[['value_2015','value_2016','value_2017','value_2018','value_2019']].max(axis=1)
#     df['max_1823'] = df[['value_2018','value_2019','value_2021','value_2022','value_2023']].max(axis=1)

#     df['range_1519'] = df['max_1519'] - df['min_1519']
#     df['range_1823'] = df['max_1823'] - df['min_1823']
    
#     return df

# def add_missing_seasonality_dates(df):
#     last_valid_index = df['period_2024'].last_valid_index()
#     dates_to_fill = pd.date_range(start=df.at[last_valid_index, 'period_2024'] + pd.Timedelta(days=7),
#                                 periods=len(df) - last_valid_index - 1, freq='7D')
#     df.loc[last_valid_index+1:, 'period_2024'] = dates_to_fill
        
#     return df

# tickvals = [0, 5, 9, 14, 18, 22, 27, 31, 36, 40, 45, 49]
# ticktext = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# def chart_seasonality(df, mapping_name, stocks_in_name, toggle_seag_range, toggle_2022,toggle_2023,toggle_2024):
#     df = df.copy()
#     df = generate_seasonality_table(df)
#     df = add_additional_seasonality_data(df)
#     df = add_missing_seasonality_dates(df)

#     def format_date(date):
#         return date.strftime('%b %d') if pd.notnull(date) else 'No Date'

#     def format_value(val, stocks_in_name):
#         if pd.isna(val):
#             return 'No data'
#         if stocks_in_name:
#             return f"{val:,.1f}" if val >= 0 else f"({abs(val):,.1f})"
#         else:
#             return f"{val:,.0f}" if val >= 0 else f"({abs(val):,.0f})"

#     traces = []
#     if not toggle_seag_range:
#         min_rng = 'min_1519'
#         max_rng = 'max_1519'
#         avg_rng = 'avg_1519'
#     else:
#         min_rng = 'min_1823'
#         max_rng = 'max_1823'
#         avg_rng = 'avg_1823'

#     traces.append(go.Scatter(
#         x=df['week_of_year'],
#         y=df[min_rng],
#         mode='lines',
#         line=dict(width=0),
#         showlegend=False,
#         hoverinfo='skip'
#     ))

#     traces.append(go.Scatter(
#         x=df['week_of_year'],
#         y=df[max_rng],
#         mode='lines',
#         fill='tonexty',
#         fillcolor='#f4f5f9',
#         line_color='#f4f5f9', 
#         showlegend=False,
#         hoverinfo='skip'
#     ))

#     traces.append(go.Scatter(
#         x=df['week_of_year'],
#         y=df[avg_rng],
#         mode='lines',
#         line=dict(color='black', dash='dot', width=1),
#         showlegend=False,
#         hoverinfo='skip'
#     ))

#     if not toggle_2024:
#         traces.append(go.Scatter(
#             x=df['week_of_year'],
#             y=df['value_2024'],
#             mode='lines',
#             name='2024',
#             hoverinfo='text',
#             text=df.apply(lambda row: f"{format_date(row['period_2024'])}: {format_value(row['value_2024'],stocks_in_name)}", axis=1),
#             line=dict(color='#c00000', dash='solid', width=2),
#         ))

#     if not toggle_2023:
#         traces.append(go.Scatter(
#             x=df['week_of_year'],
#             y=df['value_2023'],
#             mode='lines',
#             name='2023',
#             hoverinfo='text',
#             line=dict(color='#e97132', dash='solid', width=2),
#             text=df.apply(lambda row: f"{format_date(row['period_2023'])}: {format_value(row['value_2023'],stocks_in_name)}", axis=1),
#         ))

#     if not toggle_2022:
#         traces.append(go.Scatter(
#             x=df['week_of_year'],
#             y=df['value_2022'],
#             mode='lines',
#             name='2022',
#             hoverinfo='text',
#             line=dict(color='#bfbec4', dash='solid', width=2),
#             text=df.apply(lambda row: f"{format_date(row['period_2022'])}: {format_value(row['value_2022'],stocks_in_name)}", axis=1),
#         ))


#     layout = go.Layout(

#         title=dict(
#             text=mapping_name,
#             y=0.97,
#             x=0.03,
#             xanchor='left',
#             yanchor='top',
#             font=dict(
#                 color='black'
#             )
#         ),   

#         xaxis=dict(
#             range=[0, len(df['week_of_year']) - 1],
#             tickmode='array',
#             tickvals=tickvals,
#             ticktext=ticktext,
#             type='category',
#             showspikes=True,
#             spikedash='solid',
#             spikecolor='grey',
#             spikethickness=0.5,
#             spikemode='across',
#             showline=True,
#             showgrid=False,
#             linecolor='black',
#             linewidth=0.5,
#             zeroline=False
#         ),
#         yaxis=dict(
#             tickformat=',.0fK',
#             showgrid=False,
#             showline=True,
#             linecolor='black',
#             linewidth=0.5,
#             zeroline=False
#         ),
#         hovermode='x unified',
#         template='plotly_white',
#         legend=dict(
#             x=0.85,
#             y=1.0,
#             xanchor='left',
#             yanchor='top',
#             orientation='v'
#         ),
#         hoverlabel=dict(
#             bgcolor="white",
#             font_size=16,
#             font_family="Open Sans",
#             bordercolor="#ccc"
#         ),
#         margin=dict(l=40, r=40, t=40, b=25),        
#         showlegend=True
#     )


#     # Return the figure as a dictionary
#     return {'data': traces, 'layout': layout}