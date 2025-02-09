import datetime
import streamlit as st
import cesta_basica
from dados_gsheets import Dados
import gerador_de_graficos_tabelas
import pandas as pd


# Carregando dados da página
filtro_data_pau_sebo = st.date_input(label='Início - Término', value=[datetime.date(2025, 1, 1), datetime.date.today()])

dados = Dados()
detalhes_tripulantes_df = dados.generate_detalhes_tripulantes_df(filtro_data_pau_sebo)
meta_pilotos_df = dados.generate_meta_pilotos_df()
dados_pessoais_df = dados.get_dados_pessoais()
descidas_df = dados.get_descidas()
aeronaves_df = dados.get_aeronaves()
esforco_aereo_df = dados.get_esforco_aereo()
militares = dados.get_militares(filtro_data_pau_sebo, filtro_aeronave=['E-99', 'R-99'], filtro_esforco_aereo=['SESQAE'])



detalhes_tripulantes_df_filtrada = detalhes_tripulantes_df.loc[(detalhes_tripulantes_df['data_voo'].dt.date)>=filtro_data_pau_sebo[0]]
descidas_df['data'] = pd.to_datetime(descidas_df['data'], format='%d/%m/%Y %H:%M:%S')
descidas_df_filtrada = descidas_df.loc[descidas_df['data'].dt.date >= filtro_data_pau_sebo[0]]

# PAU DE SEBO
grafico_pau_de_sebo, pau_de_sebo_dados = gerador_de_graficos_tabelas.gerar_grafico_pau_de_sebo(
    detalhes_tripulantes_df=detalhes_tripulantes_df_filtrada,
    meta_pilotos_df=meta_pilotos_df,
    dados_pessoais_df=dados_pessoais_df)

    
if st.checkbox(label='Mostrar Dados - Pau de Sebo', key='pau_de_sebo_checkbox'):
    st.dataframe(pau_de_sebo_dados.drop(columns=[
        'Total_minutos',
        'meta_comprep_minutos',
        'meta_esquadrao_minutos'
    ]))
st.altair_chart(grafico_pau_de_sebo, use_container_width=True)

# ADAPTAÇÃO
st.markdown('#### Adaptação Pilotos')

grafico_adaptacao, adaptacao_dados = gerador_de_graficos_tabelas.gerar_grafico_adaptacao(
    detalhes_tripulantes_df=detalhes_tripulantes_df_filtrada,
    dados_pessoais_df=dados_pessoais_df)

if st.checkbox(label='Mostrar Dados - Adaptação Pilotos'):
    st.dataframe(adaptacao_dados, use_container_width=True)
st.altair_chart(grafico_adaptacao, use_container_width=True)

# CESTA BÁSICA
st.markdown("#### Cesta Básica")
trimestre_atual = (int(datetime.datetime.today().month) + 2) // 3
filtro_cesta_basica_trimestre = st.selectbox(label='Trimestre',
                                             options=[f"{trimestre_numero}º Trimestre" for trimestre_numero in [1,
                                                                                                                2,
                                                                                                                3,
                                                                                                                4]],
                                             index=trimestre_atual - 1)
numero_trimestre_selecionado = int(filtro_cesta_basica_trimestre.split(' ')[0][0])

cesta_basica_trimestre = cesta_basica.gerar_cesta_basica(trimestre=numero_trimestre_selecionado,
                                                         detalhes_tripulantes_df=detalhes_tripulantes_df_filtrada,
                                                         descidas_df=descidas_df_filtrada,
                                                         dados_pessoais_df=dados_pessoais_df)
st.dataframe(cesta_basica_trimestre, use_container_width=True)
st.dataframe(adaptacao_dados)