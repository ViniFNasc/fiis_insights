import pandas as pd
import datetime


class GetTopFiis:

    def __init__(self):
        self.date = datetime.datetime.now().date()
        self.path_analysis = 'database/analysis/'
        self.path_fiis_ifix = 'database/ifix/FIIs_IFIX.csv'
        self.list_fiis_ifix = self.get_fiis_ifix()
    
    def get_fiis_ifix(self):
        df_fiis_ifix = pd.read_csv(self.path_fiis_ifix,encoding='latin-1',sep=';',skiprows=1)
        df_fiis_ifix = df_fiis_ifix.reset_index()
        df_fiis_ifix.columns = ['Código', 'Ação', 'Tipo', 'Qtde. Teórica', 'Part. (%)','N/A']
        df_fiis_ifix = df_fiis_ifix.drop(columns=['N/A'])
        print(df_fiis_ifix['Código'].tolist())
        return df_fiis_ifix['Código'].tolist()

    def get_anchor_reits(self,df_fundamentus,anchor_reits_parameters):
        
        df_filtro = df_fundamentus
        df_filtro = df_filtro[df_filtro['papel'].isin(self.list_fiis_ifix)]  # Filtrando apenas os FIIs do IFIX

        filtered_dict = {
            k: v for k, v in anchor_reits_parameters.items()
            if v not in ['','*',None]
        }

        list_cols_values = [
            k for k in filtered_dict
            if 'value' in k
        ]

        list_cols_weights = [
            k for k in filtered_dict
            if 'weight' in k
        ]

        # Making the filters
        for col in list_cols_values:
            col_name = col.replace('_value','')
            df_filtro = df_filtro.query(f'{col_name} {filtered_dict[col]}')

        # Adding the weight analysis
        for col in list_cols_weights:
                            
            col_name = col.replace('_weight','')
            df_filtro[col] = ((df_filtro[col_name] - df_filtro[col_name].min()) /(df_filtro[col_name].max() - df_filtro[col_name].min())) # Normlizando as colunas entre 0 e 1
            df_filtro[col] = df_filtro[col] * float(filtered_dict[col])

        df_filtro['score'] = 0.0
        list_cols_weights = df_filtro.columns[df_filtro.columns.str.contains('_weight')]
        for col in list_cols_weights:
            df_filtro['score'] = df_filtro['score'] + df_filtro[col]

        df_filtro.drop(columns=list_cols_weights,inplace=True)
        df_filtro = df_filtro.sort_values(by='score',ascending=False)

        df_filtro.to_csv(self.path_analysis + f'anchor_reits_{self.date}.csv', index=False)

        return df_filtro
    
    def get_undervalued_reits(self,df_fundamentus,opportunity_reits_parameters):
        
        df_filtro = df_fundamentus
        df_filtro = df_filtro[df_filtro['papel'].isin(self.list_fiis_ifix)] # Filtrando apenas os FIIs do IFIX

        filtered_dict = {
            k: v for k, v in opportunity_reits_parameters.items()
            if v not in ['','*',None]
        }

        list_cols_values = [
            k for k in filtered_dict
            if 'underval' in k
        ]

        list_cols_weights = [
            k for k in filtered_dict
            if 'weight' in k
        ]

        # Making the filters
        for col in list_cols_values:
            col_name = col.replace('_underval','')
            df_filtro = df_filtro.query(f'{col_name}{filtered_dict[col]}')

        # Adding the weight analysis
        for col in list_cols_weights:
            col_name = col.replace('_weight','')
            df_filtro[col] = ((df_filtro[col_name] - df_filtro[col_name].min()) /(df_filtro[col_name].max() - df_filtro[col_name].min())) # Normlizando as colunas entre 0 e 1
            df_filtro[col] = df_filtro[col] * float(filtered_dict[col])

        df_filtro['score'] = 0.0
        list_cols_weights = df_filtro.columns[df_filtro.columns.str.contains('_weight')]
        for col in list_cols_weights:
            df_filtro['score'] = df_filtro['score'] + df_filtro[col]

        df_filtro.drop(columns=list_cols_weights,inplace=True)
        df_filtro = df_filtro.sort_values(by='score',ascending=False)

        df_filtro = df_filtro.head(20)

        df_filtro.to_csv(self.path_analysis + f'undervalued_reits_{self.date}.csv', index=False)

        return df_filtro