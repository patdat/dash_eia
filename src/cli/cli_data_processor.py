import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

class CLIDataProcessor:
    def __init__(self, data_path='data/cli/companylevelimports_crude.parquet'):
        self.data_path = data_path
        self.df = None
        self.load_data()
    
    def load_data(self):
        self.df = pd.read_parquet(self.data_path)
        self.df['RPT_PERIOD'] = pd.to_datetime(self.df['RPT_PERIOD'])
        
        # Calculate days in each month for kbd conversion
        # Get the last day of each month
        self.df['DAYS_IN_MONTH'] = self.df['RPT_PERIOD'].dt.daysinmonth
        
        # Store original QUANTITY in thousand barrels for reference
        self.df['QUANTITY_MB'] = self.df['QUANTITY']
        
        # Convert QUANTITY to kbd (thousands of barrels per day)
        # QUANTITY is monthly total in thousand barrels, divide by days in month
        self.df['QUANTITY'] = self.df['QUANTITY_MB'] / self.df['DAYS_IN_MONTH']
        
        self.df['YEAR'] = self.df['RPT_PERIOD'].dt.year
        self.df['MONTH'] = self.df['RPT_PERIOD'].dt.month
        self.df['YEAR_MONTH'] = self.df['RPT_PERIOD'].dt.strftime('%Y-%m')
        
        self.df['API_CATEGORY'] = pd.cut(
            self.df['APIGRAVITY'],
            bins=[0, 22, 31, 100],
            labels=['Heavy (<22)', 'Medium (22-31)', 'Light (>31)']
        )
        
        self.df['SULFUR_CATEGORY'] = pd.cut(
            self.df['SULFUR'],
            bins=[-np.inf, 0.5, 1.5, np.inf],
            labels=['Sweet (<0.5%)', 'Medium (0.5-1.5%)', 'Sour (>1.5%)']
        )
    
    def get_date_filtered_data(self, start_date=None, end_date=None):
        df = self.df.copy()
        if start_date:
            df = df[df['RPT_PERIOD'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['RPT_PERIOD'] <= pd.to_datetime(end_date)]
        return df
    
    @lru_cache(maxsize=32)
    def get_market_summary(self, period_months=1):
        latest_date = self.df['RPT_PERIOD'].max()
        start_date = latest_date - pd.DateOffset(months=period_months)
        
        current = self.df[self.df['RPT_PERIOD'] == latest_date]
        previous = self.df[self.df['RPT_PERIOD'] == start_date]
        
        summary = {
            'current_date': latest_date,
            'total_volume_current': current['QUANTITY'].sum(),
            'total_volume_previous': previous['QUANTITY'].sum() if not previous.empty else 0,
            'volume_change_pct': 0,
            'active_importers': current['R_S_NAME'].nunique(),
            'source_countries': current['CNTRY_NAME'].nunique(),
            'avg_api': current['APIGRAVITY'].mean(),
            'avg_sulfur': current['SULFUR'].mean(),
            'top_padd': current.groupby('PORT_PADD')['QUANTITY'].sum().idxmax()
        }
        
        if summary['total_volume_previous'] > 0:
            summary['volume_change_pct'] = ((summary['total_volume_current'] - summary['total_volume_previous']) / 
                                           summary['total_volume_previous']) * 100
        
        return summary
    
    def get_supply_disruption_alerts(self, threshold_pct=30):
        latest_date = self.df['RPT_PERIOD'].max()
        prev_date = latest_date - pd.DateOffset(months=1)
        
        # Use QUANTITY_MB (thousand barrels) for volume impact calculation
        current_mb = self.df[self.df['RPT_PERIOD'] == latest_date].groupby('CNTRY_NAME')['QUANTITY_MB'].sum()
        previous_mb = self.df[self.df['RPT_PERIOD'] == prev_date].groupby('CNTRY_NAME')['QUANTITY_MB'].sum()
        
        # Use QUANTITY (kbd) for display of current volumes
        current_kbd = self.df[self.df['RPT_PERIOD'] == latest_date].groupby('CNTRY_NAME')['QUANTITY'].sum()
        previous_kbd = self.df[self.df['RPT_PERIOD'] == prev_date].groupby('CNTRY_NAME')['QUANTITY'].sum()
        
        alerts = []
        for country in previous_mb.index:
            prev_mb_vol = previous_mb.get(country, 0)
            curr_mb_vol = current_mb.get(country, 0)
            prev_kbd_vol = previous_kbd.get(country, 0)
            curr_kbd_vol = current_kbd.get(country, 0)
            
            if prev_mb_vol > 0:
                pct_change = ((curr_mb_vol - prev_mb_vol) / prev_mb_vol) * 100
                
                if abs(pct_change) >= threshold_pct:
                    affected_companies = self.df[
                        (self.df['RPT_PERIOD'] == latest_date) & 
                        (self.df['CNTRY_NAME'] == country)
                    ]['R_S_NAME'].nunique()
                    
                    alerts.append({
                        'Country': country,
                        'Change %': round(pct_change, 1),
                        'Volume Impact (MB)': round(curr_mb_vol - prev_mb_vol, 0),  # Total thousand barrels change
                        'Current kbd': round(curr_kbd_vol, 1),  # Current volume in kbd
                        'Affected Companies': affected_companies,
                        'Signal': 'DISRUPTION' if pct_change < 0 else 'SURGE'
                    })
        
        return pd.DataFrame(alerts).sort_values('Change %')
    
    def get_top_importers(self, n=10, period_months=None):
        df = self.df.copy()
        if period_months:
            latest_date = df['RPT_PERIOD'].max()
            start_date = latest_date - pd.DateOffset(months=period_months)
            df = df[df['RPT_PERIOD'] >= start_date]
        
        # First aggregate by company and month to get monthly totals
        monthly = df.groupby(['R_S_NAME', 'RPT_PERIOD']).agg({
            'QUANTITY_MB': 'sum',
            'DAYS_IN_MONTH': 'first'  # Take first since all records in month have same days
        })
        
        # Now aggregate by company
        top = monthly.groupby('R_S_NAME').agg({
            'QUANTITY_MB': 'sum',  # Total thousand barrels
            'DAYS_IN_MONTH': 'sum'  # Total days across all months
        })
        
        # Count number of months for each company to get proper average
        month_counts = monthly.groupby('R_S_NAME').size()
        top = top.join(month_counts.rename('MONTH_COUNT'))
        
        # Add other statistics from original data
        other_stats = df.groupby('R_S_NAME').agg({
            'CNTRY_NAME': 'nunique',
            'APIGRAVITY': 'mean',
            'SULFUR': 'mean',
            'PORT_PADD': lambda x: x.value_counts().index[0] if len(x) > 0 else None
        }).round(2)
        
        top = top.join(other_stats)
        
        # Calculate average kbd properly: total barrels / total days
        top['Avg kbd'] = (top['QUANTITY_MB'] / top['DAYS_IN_MONTH']).round(1)
        
        top = top.drop(['QUANTITY_MB', 'DAYS_IN_MONTH', 'MONTH_COUNT'], axis=1)
        top.columns = ['Source Countries', 'Avg API', 'Avg Sulfur', 'Primary PADD', 'Avg kbd']
        
        # Reorder columns
        top = top[['Avg kbd', 'Source Countries', 'Avg API', 'Avg Sulfur', 'Primary PADD']]
        
        # Calculate market share based on average kbd
        top['Market Share %'] = (top['Avg kbd'] / top['Avg kbd'].sum() * 100).round(1)
        
        return top.sort_values('Avg kbd', ascending=False).head(n)
    
    def get_country_analysis(self, n=10):
        # First aggregate by country and month
        monthly = self.df.groupby(['CNTRY_NAME', 'RPT_PERIOD']).agg({
            'QUANTITY_MB': 'sum',
            'DAYS_IN_MONTH': 'first'
        })
        
        # Now aggregate by country
        country_stats = monthly.groupby('CNTRY_NAME').agg({
            'QUANTITY_MB': 'sum',
            'DAYS_IN_MONTH': 'sum'
        })
        
        # Add other statistics
        other_stats = self.df.groupby('CNTRY_NAME').agg({
            'R_S_NAME': 'nunique',
            'APIGRAVITY': 'mean',
            'SULFUR': 'mean',
            'PORT_PADD': lambda x: x.value_counts().index[0] if len(x) > 0 else None
        }).round(2)
        
        country_stats = country_stats.join(other_stats)
        
        # Calculate average kbd
        country_stats['Avg kbd'] = (country_stats['QUANTITY_MB'] / country_stats['DAYS_IN_MONTH']).round(1)
        country_stats = country_stats.drop(['QUANTITY_MB', 'DAYS_IN_MONTH'], axis=1)
        
        country_stats.columns = ['Importers', 'Avg API', 'Avg Sulfur', 'Primary PADD', 'Avg kbd']
        country_stats = country_stats[['Avg kbd', 'Importers', 'Avg API', 'Avg Sulfur', 'Primary PADD']]
        country_stats['Market Share %'] = (country_stats['Avg kbd'] / country_stats['Avg kbd'].sum() * 100).round(1)
        
        return country_stats.sort_values('Avg kbd', ascending=False).head(n)
    
    def get_padd_summary(self):
        # First aggregate by PADD and month
        monthly = self.df.groupby(['PORT_PADD', 'RPT_PERIOD']).agg({
            'QUANTITY_MB': 'sum',
            'DAYS_IN_MONTH': 'first'
        })
        
        # Now aggregate by PADD
        padd_stats = monthly.groupby('PORT_PADD').agg({
            'QUANTITY_MB': 'sum',
            'DAYS_IN_MONTH': 'sum'
        })
        
        # Add other statistics
        other_stats = self.df.groupby('PORT_PADD').agg({
            'R_S_NAME': 'nunique',
            'CNTRY_NAME': 'nunique',
            'APIGRAVITY': 'mean',
            'SULFUR': 'mean'
        }).round(2)
        
        padd_stats = padd_stats.join(other_stats)
        
        # Calculate average kbd
        padd_stats['Avg kbd'] = (padd_stats['QUANTITY_MB'] / padd_stats['DAYS_IN_MONTH']).round(1)
        padd_stats = padd_stats.drop(['QUANTITY_MB', 'DAYS_IN_MONTH'], axis=1)
        
        padd_stats.columns = ['Companies', 'Countries', 'Avg API', 'Avg Sulfur', 'Avg kbd']
        padd_stats = padd_stats[['Avg kbd', 'Companies', 'Countries', 'Avg API', 'Avg Sulfur']]
        padd_stats['Market Share %'] = (padd_stats['Avg kbd'] / padd_stats['Avg kbd'].sum() * 100).round(1)
        padd_stats.index = [f'PADD {int(x)}' for x in padd_stats.index]
        
        return padd_stats.sort_values('Avg kbd', ascending=False)
    
    def get_quality_distribution(self):
        api_dist = self.df.groupby('API_CATEGORY')['QUANTITY'].sum()
        sulfur_dist = self.df.groupby('SULFUR_CATEGORY')['QUANTITY'].sum()
        
        quality_df = pd.DataFrame({
            'API Distribution': api_dist,
            'Sulfur Distribution': sulfur_dist
        }).fillna(0)
        
        for col in quality_df.columns:
            quality_df[f'{col} %'] = (quality_df[col] / quality_df[col].sum() * 100).round(1)
        
        return quality_df
    
    def get_monthly_trends(self, n_months=12):
        latest_date = self.df['RPT_PERIOD'].max()
        start_date = latest_date - pd.DateOffset(months=n_months)
        
        monthly = self.df[self.df['RPT_PERIOD'] > start_date].groupby('RPT_PERIOD').agg({
            'QUANTITY': 'sum',
            'R_S_NAME': 'nunique',
            'CNTRY_NAME': 'nunique',
            'APIGRAVITY': 'mean',
            'SULFUR': 'mean'
        }).round(2)
        
        monthly.columns = ['Volume', 'Companies', 'Countries', 'Avg API', 'Avg Sulfur']
        monthly['Volume'] = monthly['Volume'].round(1)
        monthly['MoM Change %'] = monthly['Volume'].pct_change() * 100
        
        return monthly.round(1)
    
    def get_company_country_matrix(self, top_n=10):
        top_companies = self.df.groupby('R_S_NAME')['QUANTITY'].sum().nlargest(top_n).index
        top_countries = self.df.groupby('CNTRY_NAME')['QUANTITY'].sum().nlargest(top_n).index
        
        filtered = self.df[
            (self.df['R_S_NAME'].isin(top_companies)) & 
            (self.df['CNTRY_NAME'].isin(top_countries))
        ]
        
        matrix = filtered.pivot_table(
            index='R_S_NAME',
            columns='CNTRY_NAME',
            values='QUANTITY',
            aggfunc='sum',
            fill_value=0
        )
        
        matrix = matrix.div(matrix.sum(axis=1), axis=0) * 100
        
        return matrix.round(1)
    
    def get_port_analysis(self, n=15):
        port_stats = self.df.groupby(['PORT_CITY', 'PORT_STATE']).agg({
            'QUANTITY': 'sum',
            'R_S_NAME': 'nunique',
            'CNTRY_NAME': 'nunique',
            'PORT_PADD': lambda x: x.iloc[0] if len(x) > 0 else None
        }).round(2)
        
        port_stats.columns = ['Total Volume', 'Companies', 'Countries', 'PADD']
        port_stats['Total Volume'] = port_stats['Total Volume'].round(1)
        port_stats['Market Share %'] = (port_stats['Total Volume'] / port_stats['Total Volume'].sum() * 100).round(1)
        port_stats = port_stats.reset_index()
        port_stats['Port'] = port_stats['PORT_CITY'] + ', ' + port_stats['PORT_STATE']
        port_stats = port_stats.drop(['PORT_CITY', 'PORT_STATE'], axis=1)
        
        return port_stats.sort_values('Total Volume', ascending=False).head(n)
    
    def get_time_series_data(self, metric='volume', groupby='month', entities=None, entity_type='company'):
        df = self.df.copy()
        
        if entities:
            if entity_type == 'company':
                df = df[df['R_S_NAME'].isin(entities)]
            elif entity_type == 'country':
                df = df[df['CNTRY_NAME'].isin(entities)]
            elif entity_type == 'padd':
                df = df[df['PORT_PADD'].isin(entities)]
        
        if groupby == 'month':
            time_col = 'RPT_PERIOD'
        elif groupby == 'year':
            time_col = 'YEAR'
        
        if metric == 'volume':
            result = df.groupby([time_col, entity_type.upper() if entity_type != 'company' else 'R_S_NAME'])['QUANTITY'].sum()
        elif metric == 'api':
            result = df.groupby([time_col, entity_type.upper() if entity_type != 'company' else 'R_S_NAME'])['APIGRAVITY'].mean()
        elif metric == 'sulfur':
            result = df.groupby([time_col, entity_type.upper() if entity_type != 'company' else 'R_S_NAME'])['SULFUR'].mean()
        
        return result.reset_index()
    
    def calculate_herfindahl_index(self, by='company'):
        if by == 'company':
            shares = self.df.groupby('R_S_NAME')['QUANTITY'].sum()
        elif by == 'country':
            shares = self.df.groupby('CNTRY_NAME')['QUANTITY'].sum()
        
        market_shares = (shares / shares.sum() * 100) ** 2
        hhi = market_shares.sum()
        
        return {
            'HHI': round(hhi, 2),
            'Concentration': 'Low' if hhi < 1500 else 'Moderate' if hhi < 2500 else 'High',
            'Top 5 Share': round(shares.nlargest(5).sum() / shares.sum() * 100, 1)
        }
    
    def get_seasonality_analysis(self):
        monthly_avg = self.df.groupby('MONTH')['QUANTITY'].mean()
        overall_avg = monthly_avg.mean()
        
        seasonality = pd.DataFrame({
            'Month': range(1, 13),
            'Avg Volume': monthly_avg.values,
            'Seasonal Factor': (monthly_avg.values / overall_avg * 100).round(1),
            'Deviation from Mean': ((monthly_avg.values - overall_avg) / overall_avg * 100).round(1)
        })
        
        seasonality['Month Name'] = pd.to_datetime(seasonality['Month'], format='%m').dt.strftime('%B')
        
        return seasonality
    
    def get_quality_arbitrage_opportunities(self):
        latest_date = self.df['RPT_PERIOD'].max()
        recent = self.df[self.df['RPT_PERIOD'] >= latest_date - pd.DateOffset(months=3)]
        
        light_sweet = recent[(recent['APIGRAVITY'] > 35) & (recent['SULFUR'] < 0.5)]
        heavy_sour = recent[(recent['APIGRAVITY'] < 25) & (recent['SULFUR'] > 1.5)]
        
        arbitrage = pd.DataFrame({
            'Metric': ['Light Sweet Volume (kbd)', 'Heavy Sour Volume (kbd)', 'L/H Ratio', 
                      'Avg Light API', 'Avg Heavy API', 'API Spread',
                      'Avg Light Sulfur', 'Avg Heavy Sulfur', 'Sulfur Spread'],
            'Value': [
                light_sweet['QUANTITY'].sum(),
                heavy_sour['QUANTITY'].sum(),
                light_sweet['QUANTITY'].sum() / heavy_sour['QUANTITY'].sum() if heavy_sour['QUANTITY'].sum() > 0 else 0,
                light_sweet['APIGRAVITY'].mean(),
                heavy_sour['APIGRAVITY'].mean(),
                light_sweet['APIGRAVITY'].mean() - heavy_sour['APIGRAVITY'].mean(),
                light_sweet['SULFUR'].mean(),
                heavy_sour['SULFUR'].mean(),
                heavy_sour['SULFUR'].mean() - light_sweet['SULFUR'].mean()
            ]
        })
        
        arbitrage['Value'] = arbitrage['Value'].round(2)
        
        return arbitrage
    
    def get_monthly_totals(self, period_months=None):
        """Get monthly totals in thousand barrels (not kbd) for specific visualizations"""
        df = self.df.copy()
        if period_months:
            latest_date = df['RPT_PERIOD'].max()
            start_date = latest_date - pd.DateOffset(months=period_months)
            df = df[df['RPT_PERIOD'] >= start_date]
        
        # Use original thousand barrels for monthly totals
        monthly = df.groupby('RPT_PERIOD')['QUANTITY_MB'].sum()
        return monthly