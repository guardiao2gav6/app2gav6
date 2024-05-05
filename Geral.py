import streamlit as st
import datetime
import time_handler
import altair as alt
from databases import registros_de_voos_df, aeronaves_df, esforco_aereo_df, planejamento_horas_df
import esforco_aereo


st.set_page_config(layout='wide',
                   page_title='2º/6º GAV - CCIAO',
                   page_icon=':airplane')

filtros_cols = st.columns([1, 1, 1, 1, 1])
with filtros_cols[0]:
    filtro_datas = st.date_input(label='Início - Término', value=[datetime.date(2024, 1, 1), datetime.date.today()])
with filtros_cols[1]:
    filtro_aeronave = st.multiselect(label='Aeronave', options=aeronaves_df['modelo'].unique())
with filtros_cols[2]:
    filtro_matricula = st.multiselect(label='Matrícula', options=aeronaves_df['Matrícula'].unique())
with filtros_cols[3]:
    filtro_grupo = st.multiselect(label='Grupo', options=esforco_aereo_df['grupo'].unique())
    lista_esforco_grupo = esforco_aereo_df.loc[esforco_aereo_df['grupo'].isin(filtro_grupo), 'esforco'].unique()
with filtros_cols[4]:
    filtro_esforco_aereo = st.multiselect(label='Esforço Aéreo', options=lista_esforco_grupo)


if not filtro_aeronave:
    filtro_aeronave = aeronaves_df['modelo'].unique()
if not filtro_matricula:
    filtro_matricula = aeronaves_df['Matrícula'].unique()
if not filtro_grupo:
    filtro_grupo = esforco_aereo_df['grupo'].unique()
if not filtro_esforco_aereo:
    filtro_esforco_aereo = esforco_aereo_df.loc[esforco_aereo_df['grupo'].isin(filtro_grupo), 'esforco'].unique()

# Tabela de Registros de Voos filtrada
registros_de_voo_df_filtrada = registros_de_voos_df.loc[
    (registros_de_voos_df['aeronave'].isin(filtro_aeronave)) &
    (registros_de_voos_df['matricula'].isin(filtro_matricula)) &
    (registros_de_voos_df['esforco_aereo'].isin(filtro_esforco_aereo)) &
    (registros_de_voos_df['data_hora_dep'].dt.date >= filtro_datas[0]) &
    (registros_de_voos_df['data_hora_pouso'].dt.date <= filtro_datas[1]
     )]

if st.checkbox('Mostrar Dados - Registros de Voo'):
    registros_de_voo_df_filtrada_exibicao = registros_de_voo_df_filtrada.copy()
    registros_de_voo_df_filtrada_exibicao['tempo_de_voo'] = \
        registros_de_voo_df_filtrada_exibicao['tempo_de_voo_minutos'].map(
            time_handler.transform_minutes_to_duration_string)

    registros_de_voo_df_filtrada_exibicao = registros_de_voo_df_filtrada_exibicao.drop(columns=['tempo_de_voo_minutos',
                                                                                                'mes',
                                                                                                'foto_parte_1'])
    registros_de_voo_df_filtrada_exibicao = registros_de_voo_df_filtrada_exibicao.set_index('IdVoo')
    st.dataframe(registros_de_voo_df_filtrada_exibicao)

# KPI's
horas_totais = esforco_aereo_df[
    (esforco_aereo_df['aeronave'].isin(filtro_aeronave)) &
    (esforco_aereo_df['esforco'].isin(filtro_esforco_aereo))
    ]['horas_alocadas_minutos'].sum()

horas_voadas = registros_de_voo_df_filtrada['tempo_de_voo_minutos'].sum()
saldo_horas = horas_totais - horas_voadas

st.markdown("# ")
st.markdown("# ")

kpis_cols = st.columns([1.5, 1, 1, 1, 1.3])
with kpis_cols[1]:
    st.metric(label='Horas Totais',
              value=time_handler.transform_minutes_to_duration_string(horas_totais),
              delta="100%",
              delta_color="off")
with kpis_cols[2]:
    st.metric(label='Horas Voadas',
              value=time_handler.transform_minutes_to_duration_string(horas_voadas),
              delta=f"{round((horas_voadas/horas_totais) * 100, 2)}%",
              delta_color="off")
with kpis_cols[3]:
    st.metric(label='Saldo de Horas',
              value=time_handler.transform_minutes_to_duration_string(saldo_horas),
              delta=f"{round((saldo_horas/horas_totais) * 100, 2)}%",
              delta_color="off")

st.markdown("## ")
st.markdown("## ")

# # Planejamento Mensal

table2 = planejamento_horas_df.groupby(by='mes')[['horas_planejadas_minutos',
                                                  'horas_voadas_minutos']].sum().reset_index()
table2['Planejado'] = table2['horas_planejadas_minutos'].map(time_handler.transform_minutes_to_duration_string)
table2['Voado'] = table2['horas_voadas_minutos'].map(time_handler.transform_minutes_to_duration_string)

# Gráfico planejamento mensal
planejamento_mensal_base = alt.Chart(table2)
voado = planejamento_mensal_base.mark_bar(color="#00e842",
                                          width=60).encode(
    x=alt.X('month(mes):O', axis=alt.Axis(labelFontSize=16)),
    y=alt.Y('sum(horas_voadas_minutos):Q', axis=alt.Axis(title='', labels=False)),
    tooltip=['Planejado:N', 'Voado:N'])

linha = voado.mark_line(opacity=0.3,
                        color="#060191",
                        strokeWidth=4,
                        strokeCap='round',
                        point=alt.OverlayMarkDef(fill='Black', size=120,)
                        ).encode(
    y=alt.Y('sum(horas_planejadas_minutos):Q')

)

rotulos_planejado = alt.Chart(table2).mark_text(
    baseline='alphabetic',
    align='center',
    dy=-20,
    fontSize=16
).encode(
    x=alt.X('month(mes):O', axis=alt.Axis(title='')),
    y=alt.Y('sum(horas_planejadas_minutos):Q', axis=alt.Axis(title='', labels=True)),
    text='Planejado',

)

rotulo_voado = alt.Chart(table2).mark_text(
    baseline='alphabetic',
    align='center',
    fontSize=16,
).encode(
    x=alt.X('month(mes):O', axis=alt.Axis(title='')),
    y=alt.Y('sum(horas_voadas_minutos):Q', axis=alt.Axis(title='', labels=False)),
    text='Voado',

)

grafico = (linha + voado + rotulos_planejado).properties(title=alt.TitleParams(
    text='Planejado vs Voado - Horas COMPREP',
    fontSize=24,
    anchor='middle'
))

st.altair_chart(grafico, use_container_width=True)

if st.checkbox(label='Mostrar dados - Planejamento horas COMPREP'):
    table3 = planejamento_horas_df
    table3['Planejado'] = table3['horas_planejadas_minutos'].map(time_handler.transform_minutes_to_duration_string)
    table3['Voado'] = table3['horas_voadas_minutos'].map(time_handler.transform_minutes_to_duration_string)
    table3 = table3.drop(columns=['horas_planejadas_minutos',
                                  'horas_voadas_minutos',
                                  'mes_numero',
                                  'horas_planejadas',
                                  'horas_voadas'])
    table3['mes'] = table3['mes'].dt.month_name()
    table3 = table3.set_index('mes')
    table3 = table3.reindex(columns=['aeronave', 'esforco', 'Planejado', 'Voado', 'observacoes'])

    cols_planejamento = st.columns([1, 1, 1])
    with cols_planejamento[0]:
        filtro_planejamento_mes = st.multiselect(label='Mês',
                                                 options=table3.index.unique(),
                                                 key='filtro_planejamento_mes')
    with cols_planejamento[1]:
        filtro_planejamento_anv = st.multiselect(label='Aeronave',
                                                 options=table3['aeronave'].unique(),
                                                 key='filtro_planejamento_anv')
    with cols_planejamento[2]:
        filtro_planejamento_esforco = st.multiselect(label='Esforço',
                                                     options=table3['esforco'].unique(),
                                                     key='filtro_planejamento_esforco')

    if not filtro_planejamento_mes:
        filtro_planejamento_mes = table3.index.unique()
    if not filtro_planejamento_anv:
        filtro_planejamento_anv = table3['aeronave'].unique()
    if not filtro_planejamento_esforco:
        filtro_planejamento_esforco = table3['esforco'].unique()

    table3_filtrada = table3.loc[(table3.index.isin(filtro_planejamento_mes)) &
                                 (table3['aeronave'].isin(filtro_planejamento_anv) &
                                 (table3['esforco'].isin(filtro_planejamento_esforco)))]

    st.dataframe(table3_filtrada, use_container_width=True)

st.markdown("#")
st.markdown("#")
st.markdown('---')
st.markdown("### Esforço Aéreo")

cols = st.columns([1, 0.2, 1])
with cols[0]:
    st.markdown('### E-99')
    st.markdown('##### COMPREP')
    E99_comprep_chart = esforco_aereo.gerar_grafico_esforco('E-99', 'COMPREP')
    st.altair_chart(E99_comprep_chart, use_container_width=True)

    st.markdown('#### COMAE')
    E99_comae_chart = esforco_aereo.gerar_grafico_esforco('E-99', 'COMAE')
    st.altair_chart(E99_comae_chart, use_container_width=True)

    st.markdown('#### DCTA')
    E99_dcta_chart = esforco_aereo.gerar_grafico_esforco('E-99', 'DCTA')
    st.altair_chart(E99_dcta_chart, use_container_width=True)

with cols[2]:
    st.markdown('### R-99')
    st.markdown('##### COMPREP')
    R99_comprep_chart = esforco_aereo.gerar_grafico_esforco('R-99', 'COMPREP')
    st.altair_chart(R99_comprep_chart, use_container_width=True)

    st.markdown('#### COMAE')
    R99_comae_chart = esforco_aereo.gerar_grafico_esforco('R-99', 'COMAE')
    st.altair_chart(R99_comae_chart, use_container_width=True)

    st.markdown('#### DCTA')
    R99_dcta_chart = esforco_aereo.gerar_grafico_esforco('R-99', 'DCTA')
    st.altair_chart(R99_dcta_chart, use_container_width=True)
