import pandas as pd
import time_handler


def carregar_dados():
    sheet_id = "1pHRfuc0vHjFLWdZ4DlX7OencLG6vIyCbtj53Jk88UR8"
    database = pd.read_excel(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx",
                             engine='openpyxl',
                             sheet_name=['Detalhes dos Tripulantes',
                                         'Registro de Voos',
                                         'Dados Pessoais',
                                         'Funções a Bordo',
                                         'Aeronaves',
                                         'Esforço Aéreo',
                                         'Planejamento Horas',
                                         'Descidas',
                                         'OPO',
                                         'Meta Horas Pilotos',
                                         'Tripulantes Sobreaviso',
                                         'Sobreaviso'])

    return database


databases = carregar_dados()
detalhes_tripulantes_sobreaviso = databases.get('Tripulantes Sobreaviso')
sobreaviso_df = databases.get('Sobreaviso')

detalhes_tripulantes_df = databases.get('Detalhes dos Tripulantes')

registros_de_voos_df = databases.get('Registro de Voos')
registros_de_voos_df['tempo_de_voo'] = registros_de_voos_df['tempo_de_voo'].astype(str)

dados_pessoais_df = databases.get('Dados Pessoais')

funcoes_a_bordo_df = databases.get('Funções a Bordo')

aeronaves_df = databases.get('Aeronaves')

esforco_aereo_df = databases.get('Esforço Aéreo')
esforco_aereo_df['horas_alocadas'] = esforco_aereo_df['horas_alocadas_minutos'].map(
    time_handler.transform_minutes_to_duration_string)
esforco_aereo_df['horas_gastas'] = esforco_aereo_df['horas_gastas_minutos'].map(
    time_handler.transform_minutes_to_duration_string)
esforco_aereo_df['saldo_horas'] = esforco_aereo_df['saldo_horas_minutos'].map(
    time_handler.transform_minutes_to_duration_string)
esforco_aereo_df = esforco_aereo_df.drop(columns=['IdEsfAer'])

planejamento_horas_df = databases.get('Planejamento Horas')

descidas_df = databases.get('Descidas')


detalhes_tripulantes_df['data_voo'] = pd.to_datetime(detalhes_tripulantes_df['data_voo'], format="%d/%m/%Y").dt.date
detalhes_tripulantes_df['posicao_a_bordo'] = detalhes_tripulantes_df['posicao_a_bordo'].fillna(True)
detalhes_tripulantes_df['posicao_a_bordo'] = detalhes_tripulantes_df['posicao_a_bordo'].map(
    lambda x: 'RSP' if x else 'LSP')

df1 = registros_de_voos_df[['IdVoo',
                            'tempo_de_voo_minutos',
                            'tempo_noturno',
                            'tempo_ifr',
                            'ifr_sem_pa',
                            'arremetidas',
                            'trafego_visual']]

detalhes_tripulantes_df = detalhes_tripulantes_df.merge(df1, how='left')
detalhes_tripulantes_df['data_voo'] = pd.to_datetime(detalhes_tripulantes_df['data_voo'])

OPO_df = databases.get('OPO')

meta_pilotos_df = databases.get('Meta Horas Pilotos').drop(columns=['meta_comprep', 'meta_esquadrao'])
meta_pilotos_df['meta_comprep'] = meta_pilotos_df['meta_comprep_minutos'].map(
    time_handler.transform_minutes_to_duration_string)
meta_pilotos_df['meta_esquadrao'] = meta_pilotos_df['meta_esquadrao_minutos'].map(
    time_handler.transform_minutes_to_duration_string)
