import pandas as pd
from utils_wps.ag_mapping import ag_mapping
from utils.data_loader import cached_loader

class DataProcessor:
    def __init__(self, file_path='./data/wps/wps_gte_2015_pivot.feather'):
        self.file_path = file_path

    def get_initial_data(self):
        """Load data using cached loader for better performance"""
        df = cached_loader.load_wps_pivot_data()
        df['period'] = df['period'].dt.strftime('%m/%d/%y')
        df.set_index('period', inplace=True)
        df = df.T
        df.reset_index(inplace=True)
        return df

    def get_ag_mapping(self, df):
        """Use cached mapping data for better performance"""
        ag_mapping_data = cached_loader.load_ag_mapping()
        
        id_to_name_mapping = {key: value['name'] for key, value in ag_mapping_data.items()}
        id_to_padd_mapping = {key: value['padd'] for key, value in ag_mapping_data.items()}
        id_to_commodity_mapping = {key: value['commodity'] for key, value in ag_mapping_data.items()}
        id_to_type_mapping = {key: value['type'] for key, value in ag_mapping_data.items()}
        id_to_uom_mapping = {key: value['uom'] for key, value in ag_mapping_data.items()}

        df.insert(1, 'name', df['id'].map(id_to_name_mapping))
        df.insert(2, 'padd', df['id'].map(id_to_padd_mapping))
        df.insert(3, 'commodity', df['id'].map(id_to_commodity_mapping))
        df.insert(4, 'type', df['id'].map(id_to_type_mapping))
        df.insert(5, 'uom', df['id'].map(id_to_uom_mapping))
        
        order_list = list(id_to_name_mapping.keys())        
        df = df.set_index('id').loc[order_list].reset_index()
        
        return df

    def get_columns_to_include(self, df, startDate, endDate):
        cols = df.columns.tolist()
        remove_cols_for_evaluation = ['id', 'name', 'padd', 'commodity', 'type', 'uom']
        for col in remove_cols_for_evaluation:
            cols.remove(col)        
        cols = pd.to_datetime(cols, format='%m/%d/%y')
        cols = cols[cols >= startDate]
        cols = cols[cols <= endDate]    
        cols = cols.strftime('%m/%d/%y').tolist()
        cols = remove_cols_for_evaluation + cols
        df = df[cols]    
        return df

    def get_table(self, start='1900-01-01', end='2030-12-31'):
        df = self.get_initial_data()
        df = self.get_ag_mapping(df)
        df = self.get_columns_to_include(df, start, end)
        return df

    def get_initial_columns(self, df):
        columnDefs = [{
            'headerName': col,
            'field': col,
            'checkboxSelection': False,
            'floatingFilter': False,
            "suppressHeaderMenuButton": True,
            'filter': 'agTextColumnFilter',
            'suppressFloatingFilterButton': True,
            'width': 100,
            'cellRenderer': 'HighlightCellRenderer',    
        } for col in df.columns]
        return columnDefs

    def column_adjustment(self, columnDefs):
        columnDefs[0]['checkboxSelection'] = True
        columnDefs[0]['width'] = 150
        columnDefs[1]['width'] = 200
        columnDefs[2]['width'] = 80
        columnDefs[3]['width'] = 110
        columnDefs[4]['width'] = 160
        columnDefs[5]['width'] = 70

        for i in range(6, len(columnDefs)):
            columnDefs[i]['valueFormatter'] = {'function': 'numberFormatter(params.value)'}
            columnDefs[i]['cellStyle'] = {'textAlign': 'right'}

        cols = [0, 1, 2, 3, 4, 5]
        for col in cols:
            columnDefs[col]['pinned'] = 'left'    
            columnDefs[col]['filter'] = 'agTextColumnFilter'
            columnDefs[col]['floatingFilter'] = True  

        columnDefs[1]['hide'] = True
        columnDefs[5]['hide'] = True

        return columnDefs

    def get_columns(self, df):
        columnDefs = self.get_initial_columns(df)
        columnDefs = self.column_adjustment(columnDefs)
        return columnDefs

    def get_data(self, start='1900-01-01', end='2030-12-31'):
        df = self.get_table(start, end)
        columnDefinitions = self.get_columns(df)
        return df, columnDefinitions