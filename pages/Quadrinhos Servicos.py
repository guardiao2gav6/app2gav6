import pandas as pd
import altair as alt
from dados_gsheets import Dados
import streamlit as st
import datetime


# Função utilizada para gerar uma coluna com o total de serviços tirados
def gerar_totais(value, table):
    total = table.loc[table['militar'] == value, 'Qtde serviços'].sum()

    return total


# Função que transforma os dados brutos de serviços (militar x data) em wide data (militar e qtde de svc por quadrinho)
def generate_chart_data(data, lista_de_militares):
    value_vars = data['cor_portugues'].unique()
    data_chart_df = data.groupby(by=['militar', 'cor_portugues'])[['cor_portugues']].count()
    data_chart_df = data_chart_df.rename(columns={'cor_portugues': 'Qtde serviços'}).reset_index()
    data_chart_df = pd.pivot_table(data_chart_df,
                                   index=['militar'],
                                   columns=['cor_portugues'],
                                   values='Qtde serviços',
                                   aggfunc='sum',
                                   fill_value=0).reset_index()

    data_chart_df = pd.DataFrame({'militar': lista_de_militares}).merge(right=data_chart_df,
                                                                        how='left',
                                                                        on='militar').fillna(0)

    data_chart_df = pd.melt(data_chart_df,
                            id_vars=['militar'],
                            value_vars=value_vars,
                            value_name='Qtde serviços',
                            var_name='cor_portugues')

    data_chart_df['Totais'] = data_chart_df['militar'].map(lambda x: gerar_totais(x, data_chart_df))

    return data_chart_df


# Função que recebe os dados e gera o gráfico
def generate_chart(data):
    data_base_chart = alt.Chart(data)
    data_chart = data_base_chart.mark_bar().encode(
        x=alt.X('militar:N',
                sort=alt.EncodingSortField(field='Qtde serviços',
                                           op='sum',
                                           order='descending'),
                axis=alt.Axis(title='',
                              labelAngle=0,
                              labelFontSize=16)),
        y=alt.Y('sum(Qtde serviços):Q',
                axis=alt.Axis(title="",
                              labels=False)),
        color=alt.Color('cor_portugues:N',
                        scale=alt.Scale(domain=['Preto', 'Vermelho', 'Roxo'],
                                        range=['rgba(0, 0, 0, 0.8)', 'rgba(255, 0, 0, 0.8)', 'rgba(173, 3, 145, 0.8)']),
                        legend=alt.Legend(title='Cor do Quadrinho',
                                          orient='top')),
        tooltip=[
            alt.Tooltip('militar:N', title='Trig: '),
            alt.Tooltip('cor_portugues:N', title='Cor: '),
            alt.Tooltip('Qtde serviços:Q', title='Qtde: ')
        ]
    )

    data_rotulos = data_base_chart.mark_text(
        baseline='bottom',
        align='center',
        fontSize=18,
        dy=-7
    ).encode(
        x=alt.X('militar:N',
                sort=alt.EncodingSortField(field='Qtde serviços',
                                           op='sum',
                                           order='descending')),
        y=alt.Y('mean(Totais):Q',
                axis=alt.Axis(title="",
                              labels=False)),
        text='mean(Totais):Q'
    )

    return data_chart + data_rotulos


# função que recebe os dados e deixa somente os Serviços Cumpridos
def filter_data(data):
    data_filtered = data.loc[data['status_decod'] == 'Serviço Cumprido']
    return data_filtered


# Carregando DADOS
dados = Dados()
OPO_df = dados.get_opo_df()
dados_pessoais_df = dados.get_dados_pessoais()
detalhes_tripulantes_sobreaviso = dados.get_detalhes_tripulantes_sobreaviso()
detalhes_tripulantes_sobreaviso_R99_final = dados.get_detalhes_tripulantes_sobreaviso_r99()


filtro_data_quadrinhos = st.date_input(label='Início - Término', value=[datetime.date(2025, 1, 1), datetime.date.today()])

detalhes_tripulantes_sobreaviso['data'] = pd.to_datetime(detalhes_tripulantes_sobreaviso['data'], format='%d/%m/%Y')
detalhes_tripulantes_sobreaviso_filtrado = detalhes_tripulantes_sobreaviso.loc[(detalhes_tripulantes_sobreaviso['data'].dt.date)>=filtro_data_quadrinhos[0]]

detalhes_tripulantes_sobreaviso_R99_final['data'] = pd.to_datetime(detalhes_tripulantes_sobreaviso_R99_final['data'], format='%d/%m/%Y')
detalhes_tripulantes_sobreaviso_r99_filtrado = detalhes_tripulantes_sobreaviso_R99_final.loc[(detalhes_tripulantes_sobreaviso_R99_final['data'].dt.date)>=filtro_data_quadrinhos[0]]

OPO_df['data'] = pd.to_datetime(OPO_df['data'], format="%d/%m/%Y")
OPO_df_filtrado = OPO_df.loc[(OPO_df['data'].dt.date) >= filtro_data_quadrinhos[0]]

# Obtendo apenas os miitares que tiram OPO ou SA
militares_opo_sa = dados_pessoais_df.loc[dados_pessoais_df['sigla_funcao'].isin(['PIL',
                                                                                 'PIL/CC-R',
                                                                                 'PIL/COTAT',
                                                                                 'CC-R']), 'trigrama'].to_list()
militares_opo = dados_pessoais_df.loc[(dados_pessoais_df['sigla_funcao'].isin(['PIL',
                                                                               'CC-R',
                                                                               'PIL/COTAT',
                                                                               'PIL/CC-R'])) |
                                      (dados_pessoais_df['trigrama'] == 'AND'), 'trigrama'].to_list()

militares_sobreaviso_R99 = dados_pessoais_df.loc[dados_pessoais_df['sigla_funcao'].isin(['PIL/COTAT',
                                                                                        'COTAT']), 'trigrama'].to_list()

#   Removendo militares que se encaixam nos padrões acima, porém não tiram serviço (CMT e S3)

# Tratamento dos dados
OPO_cumpridos = filter_data(OPO_df_filtrado)
OPO_chart_data = generate_chart_data(OPO_cumpridos, militares_opo)
OPO_chart = generate_chart(OPO_chart_data)

SOBREAVISO_CUMPRIDO = filter_data(detalhes_tripulantes_sobreaviso_filtrado)
SOBREAVISO_chart_data = generate_chart_data(SOBREAVISO_CUMPRIDO, militares_opo_sa)
SOBREAVISO_chart = generate_chart(SOBREAVISO_chart_data)

SOBREAVISO_R99_CUMPRIDO = filter_data(detalhes_tripulantes_sobreaviso_r99_filtrado)
SOBREAVISO_R99_chart_data = generate_chart_data(SOBREAVISO_R99_CUMPRIDO, militares_sobreaviso_R99)
SOBREAVISO_R99_chart = generate_chart(SOBREAVISO_R99_chart_data)

# Concatenando as tabelas de serviços para obter o total
TOTAL_data = pd.concat([OPO_chart_data, SOBREAVISO_chart_data, SOBREAVISO_R99_chart_data])
TOTAL_data = TOTAL_data.drop(columns='Totais')
TOTAL_data = TOTAL_data.groupby(by=['militar', 'cor_portugues'])[['Qtde serviços']].sum().reset_index()
TOTAL_data['Totais'] = TOTAL_data['militar'].map(lambda x: gerar_totais(x, TOTAL_data))
total_chart = generate_chart(TOTAL_data)

# VISUALIZAÇÃO
st.markdown('### Total de Serviços - OPO + CAV + R-99')
st.altair_chart(total_chart, use_container_width=True)
st.markdown('---')

st.markdown('#### OPO')
if st.checkbox('Mostrar Dados - OPO'):
    st.dataframe(OPO_cumpridos)
st.altair_chart(OPO_chart, use_container_width=True)

st.markdown("#### Sobreaviso CAV")
if st.checkbox('Mostrar Dados - SOBREAVISO'):
    st.dataframe(SOBREAVISO_CUMPRIDO)
st.altair_chart(SOBREAVISO_chart, use_container_width=True)

st.markdown('#### Sobreaviso R-99')
if st.checkbox('Mostrar Dados - SOBREAVISO R99'):
    st.dataframe(SOBREAVISO_R99_CUMPRIDO)
st.altair_chart(SOBREAVISO_R99_chart, use_container_width=True)
