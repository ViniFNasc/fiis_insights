import pandas as pd
import datetime


class GetTopFiis:

    def __init__(self):
        self.date = datetime.datetime.now().date()
        self.path_analysis = 'database/analysis/'
        

    def get_anchor_reits(self,df_fundamentus,anchor_reits_parameters):
        
        df_filtro = df_fundamentus

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