import pandas as pd
import datetime
import funcoes_tripulantes


def checar_adaptacao(x):
    if x >= 0:
        return x
    else:
        return 'Des.'


def gerar_adaptacao(detalhes_tripulantes_df,
                    dados_pessoais_df):

    tempo_para_desadaptar_pilotos = {'AL': 20,
                                     '1P': 35,
                                     'IN': 45}
    tempo_para_desadaptar_tripulantes = {
        'AC': 35,
        'MC': 45,
        'IC': 60,
        'AD-R': 35,
        'CO-R': 60,
        'ID-R': 75,
        'AB-R': 35,
        'CC-R': 60,
        'IB-R': 75,
        'AJ': 35,
        'CT': 45,
        'IJ': 60,
        'A3': 35,
        'O3': 45,
        'I3': 60,
        'A1': 35,
        'O1': 45,
        'I1': 60,
        'AA-E': 35,
        'MA-E': 45,
        'IA-E': 60,
        'AA-R': 35,
        'MA-R': 45,
        'IA-R': 60,
    }
    lista_funcoes_pilotos = ['AL', 'IN', '2P', '1P']
    tripulantes = funcoes_tripulantes.funcoes_tripulantes(dados_pessoais_df)

    ultimos_voos_pilotos = detalhes_tripulantes_df.loc[detalhes_tripulantes_df['funcao_a_bordo'].isin(
        lista_funcoes_pilotos), ['tripulante', 'funcao_a_bordo', 'data_voo']]

    ultimos_voos_pilotos = ultimos_voos_pilotos.groupby(by='tripulante')[['data_voo']].max().reset_index()

    ultimos_voos_pilotos['data_voo'] = pd.to_datetime(ultimos_voos_pilotos['data_voo'], format='%d/%m/%Y')

    adaptacao_pilotos = tripulantes.loc[tripulantes['funcao_a_bordo'].isin(lista_funcoes_pilotos)].reset_index()

    adaptacao_pilotos = adaptacao_pilotos.rename(columns={'trigrama': 'tripulante'})

    adaptacao_pilotos['dias_para_desadaptar'] = adaptacao_pilotos['funcao_a_bordo'].map(
        lambda x: tempo_para_desadaptar_pilotos.get(x))

    adaptacao_pilotos = adaptacao_pilotos.merge(right=ultimos_voos_pilotos, how='left', on='tripulante')

    adaptacao_pilotos = adaptacao_pilotos.fillna(pd.to_datetime('31/12/2023', format='%d/%m/%Y'))

    adaptacao_pilotos['voar_ate'] = adaptacao_pilotos['data_voo'] + pd.to_timedelta(
        adaptacao_pilotos['dias_para_desadaptar'], unit='D')

    adaptacao_pilotos['dias_restantes'] = (adaptacao_pilotos['voar_ate'] - datetime.datetime.now()).dt.days + 1

    adaptacao_pilotos['dias_sem_voar'] = (datetime.datetime.now() - adaptacao_pilotos['data_voo']).dt.days

    adaptacao_pilotos = adaptacao_pilotos.drop(columns=['index'])
    adaptacao_pilotos['label_dias_restantes'] = adaptacao_pilotos['dias_restantes'].map(checar_adaptacao)
    adaptacao_pilotos['dias_sem_voar_grafico'] = adaptacao_pilotos['dias_sem_voar']

    for index, row in adaptacao_pilotos.iterrows():
        qualificacao_op = row['funcao_a_bordo']
        if row['dias_restantes'] <= 0:
            adaptacao_pilotos.loc[index, 'dias_sem_voar_grafico'] = tempo_para_desadaptar_pilotos[qualificacao_op]

    ultimos_voo_tripulantes = detalhes_tripulantes_df.loc[~detalhes_tripulantes_df['funcao_a_bordo'].isin(
        lista_funcoes_pilotos), ['tripulante', 'funcao_a_bordo', 'data_voo']]

    ultimos_voo_tripulantes = ultimos_voo_tripulantes.groupby(by='tripulante')[['data_voo']].max().reset_index()

    ultimos_voo_tripulantes['data_voo'] = pd.to_datetime(ultimos_voo_tripulantes['data_voo'], format='%d/%m/%Y')

    adaptacao_tripulantes_df = tripulantes.loc[~tripulantes['funcao_a_bordo'].isin(lista_funcoes_pilotos)].reset_index()
    adaptacao_tripulantes_df = adaptacao_tripulantes_df.rename(columns={'trigrama': 'tripulante'})
    adaptacao_tripulantes_df['dias_para_desadaptar'] = adaptacao_tripulantes_df['funcao_a_bordo'].map(
        lambda x: tempo_para_desadaptar_tripulantes.get(x))

    adaptacao_tripulantes_df = adaptacao_tripulantes_df.merge(right=ultimos_voo_tripulantes,
                                                              how='left',
                                                              on='tripulante')
    adaptacao_tripulantes_df = adaptacao_tripulantes_df.fillna(pd.to_datetime('31/12/2023', format='%d/%m/%Y'))

    adaptacao_tripulantes_df['voar_ate'] = adaptacao_tripulantes_df['data_voo'] + pd.to_timedelta(
        adaptacao_tripulantes_df['dias_para_desadaptar'], unit='D')

    adaptacao_tripulantes_df['dias_restantes'] = (adaptacao_tripulantes_df['voar_ate'] -
                                                  datetime.datetime.now()).dt.days + 1

    adaptacao_tripulantes_df['dias_sem_voar'] = (datetime.datetime.now() - adaptacao_tripulantes_df['data_voo']).dt.days
    adaptacao_tripulantes_df = adaptacao_tripulantes_df.drop(columns=['index'])

    return adaptacao_pilotos, adaptacao_tripulantes_df
