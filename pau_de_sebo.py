import pandas as pd
import time_handler
import funcoes_tripulantes
import streamlit as st


def pau_de_sebo_demais_tripulantes(detalhes_tripulantes_df,
                                   dados_pessoais_df,
                                   funcao,
                                   funcoes_agrupadas):
    

    tripulantes = funcoes_tripulantes.funcoes_tripulantes(dados_pessoais_df)
    tripulantes.rename(columns={'trigrama': 'tripulante'}, inplace=True)

    tripulantes_unicos = tripulantes.loc[tripulantes['funcao_a_bordo'].isin(funcoes_agrupadas[funcao])].reset_index(drop=True)
    tripulantes_unicos = tripulantes_unicos.drop(columns='funcao_a_bordo')
    
    pau_sebo_tripulantes_parcial = detalhes_tripulantes_df.loc[(detalhes_tripulantes_df['aeronave'] != 'SIM C-99') &
                                                       (detalhes_tripulantes_df['funcao_a_bordo'].isin(funcoes_agrupadas[funcao]))]

    pau_sebo_tripulantes_parcial = pau_sebo_tripulantes_parcial.groupby(
        by=['tripulante',
        'funcao_a_bordo'])[['tempo_de_voo_minutos']].sum().reset_index()

    pau_sebo_tripulantes_parcial = pd.pivot_table(pau_sebo_tripulantes_parcial,
                                            index='tripulante',
                                            values='tempo_de_voo_minutos',
                                            columns='funcao_a_bordo',
                                            aggfunc='sum',
                                            fill_value=0)
    
    pau_sebo_tripulantes = tripulantes_unicos.merge(right=pau_sebo_tripulantes_parcial, how='left', on='tripulante').fillna(0)
    pau_sebo_tripulantes['tempo_de_voo_minutos'] = pau_sebo_tripulantes.loc[:, pau_sebo_tripulantes.columns.difference(['tripulante'])].sum(axis=1)
    

    return pau_sebo_tripulantes


def pau_de_sebo_pilotos(detalhes_tripulantes_df,
                        meta_pilotos_df,
                        dados_pessoais_df):

    tripulantes = funcoes_tripulantes.funcoes_tripulantes(dados_pessoais_df)
    tripulantes.rename(columns={'trigrama': 'tripulante'}, inplace=True)

    pilotos_unicos = tripulantes.loc[tripulantes['funcao_a_bordo'].isin(['AL',
                                                                         '1P',
                                                                         '2P',
                                                                         'IN'])].reset_index(drop=True)
    pilotos_unicos = pilotos_unicos.drop(columns='funcao_a_bordo')

    # Filtra apenas militares que voaram com as funções de IN, AL, 1P, 2P.
    pau_sebo_pilotos_parcial = detalhes_tripulantes_df.loc[(detalhes_tripulantes_df['funcao_a_bordo'].isin(['IN',
                                                                                                            'AL',
                                                                                                            '1P',
                                                                                                            '2P'])) &
                                                           (detalhes_tripulantes_df['aeronave'] != 'SIM C-99')]
    pau_sebo_pilotos_parcial = pau_sebo_pilotos_parcial.groupby(
        by=['tripulante',
            'posicao_a_bordo'])[['tempo_de_voo_minutos']].sum().reset_index()
    pau_sebo_pilotos_parcial = pd.pivot_table(pau_sebo_pilotos_parcial,
                                              index='tripulante',
                                              values='tempo_de_voo_minutos',
                                              columns='posicao_a_bordo',
                                              aggfunc='sum',
                                              fill_value=0)
    pau_sebo_pilotos = pilotos_unicos.merge(right=pau_sebo_pilotos_parcial, how='left', on='tripulante').fillna(0)
    pau_sebo_pilotos['Total_minutos'] = pau_sebo_pilotos['LSP'] + pau_sebo_pilotos['RSP']
    pau_sebo_pilotos['LSP_label'] = pau_sebo_pilotos['LSP'].map(time_handler.transform_minutes_to_duration_string)
    pau_sebo_pilotos['RSP_label'] = pau_sebo_pilotos['RSP'].map(time_handler.transform_minutes_to_duration_string)
    pau_sebo_pilotos['Total'] = pau_sebo_pilotos['Total_minutos'].map(time_handler.transform_minutes_to_duration_string)
    pau_sebo_pilotos = pau_sebo_pilotos.sort_values('Total', ascending=False)
    pau_sebo_pilotos = pau_sebo_pilotos.merge(right=meta_pilotos_df, how='left', on='tripulante')

    return pau_sebo_pilotos
