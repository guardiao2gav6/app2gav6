from dados_gsheets import Dados
import streamlit as st
import datetime
import altair as alt
import pandas as pd
import time_handler
from models.militar import Militar
from copy import deepcopy
from models import constantes


def somar_totais_de_horas(horas_militares_filtrado_grupo):
  result = []
  for horas_militar_filtrado in horas_militares_filtrado_grupo:
    
    totais_horas = sum(valor for chave, valor in horas_militar_filtrado.items() if isinstance(valor, int))
    
    horas_militar_filtrado['Totais'] = totais_horas
    
    horas_militar_filtrado = {
      **horas_militar_filtrado,
      **{chave + '_hhmm': time_handler.transform_minutes_to_duration_string(valor) for chave, valor in horas_militar_filtrado.items() if isinstance(valor, int)}
    }
    
    horas_militar_filtrado = {'trigrama': horas_militar_filtrado['trigrama'],
    **horas_militar_filtrado}
    result.append(deepcopy(horas_militar_filtrado))
  return result


# Carregando dados
dados = Dados()
aeronaves = dados.get_aeronaves()['modelo'].unique()
esforco_aereo = dados.get_esforco_aereo()['esforco'].unique()

# FILTROS
filtro_periodo = st.date_input(label='Período', value=[datetime.date(2025, 1, 1), datetime.date.today()], key='periodo')

voos = dados.generate_registros_voos_df(filtro_periodo)
st.dataframe(voos)

filtro_aeronave = st.multiselect(label='Aeronave', options=aeronaves)
if not filtro_aeronave:
  filtro_aeronave = aeronaves

filtro_esforco_aereo = st.multiselect(label='Esforço Aéreo', options=esforco_aereo)
if not filtro_esforco_aereo:
  filtro_esforco_aereo = esforco_aereo

filtro_grupo_de_funcoes = st.selectbox(label='Função à Bordo', options=constantes.funcoes_agrupadas_sem_valores)

# Extraindo dados de voo apenas do período selecionado
militares = dados.get_militares(filtro_periodo, filtro_aeronave, filtro_esforco_aereo, filtro_grupo_de_funcoes)

horas_militares = list(map(lambda x: x.horas_militar(), militares))
horas_militares_somadas = somar_totais_de_horas(horas_militares)
df_horas_militares = pd.DataFrame(horas_militares_somadas)

funcoes = constantes.funcoes_agrupadas_sem_valores[filtro_grupo_de_funcoes]

df_long = df_horas_militares.melt(id_vars=[id_var for id_var in df_horas_militares.columns if id_var not in funcoes],
                                  value_vars=funcoes,
                                  var_name='funcao_posicao_a_bordo',
                                  value_name='horas')
base = alt.Chart(df_long)

grafico = base.mark_bar(size=20).encode(
  x=alt.X('trigrama:N',
  sort=alt.EncodingSortField(
    field='horas',
    op='sum',
    order='descending'
  ),
  axis=alt.Axis(title='',
                            labelAngle=-0,
                            labelFontSize=16,
                            ticks=False)),
  y=alt.Y('horas:Q', axis=alt.Axis(title='',
                                        labels=False)),
  color=alt.Color('funcao_posicao_a_bordo:N',
  scale=alt.Scale(domain=funcoes,
  range=['#219ebc', '#023047', '#fb8500', '#1a8273']),
        legend=alt.Legend(title='Função/Posição à Bordo',
                            orient='top'))
)

text = base.mark_text(
    fontSize=16,
    dy=-20,
    color='#747575'
).encode(
    x=alt.X('trigrama:N',
            sort=alt.EncodingSortField(field='horas', op='sum', order='descending'),
            axis=alt.Axis(labelAngle=-0)
            ),
    y='sum(horas):Q',
    text='Totais_hhmm:N',
)

st.altair_chart((grafico + text), use_container_width=True)

# ADAPTAÇÃO
adaptacao_militares = list(map(lambda x: x.adaptacao(), militares))

adaptacao_militares = [item for sublista in adaptacao_militares for item in sublista if item['funcao_a_bordo'] in grupo]

df_adaptacao_militares = pd.DataFrame(adaptacao_militares)
df_adaptacao_militares['dias_para_desadaptar'] = df_adaptacao_militares['dias_para_desadaptar'].dt.days

df_adaptacao_militares = df_adaptacao_militares.sort_values(by=['funcao_a_bordo', 'dias_sem_voar'], ascending=False)

adaptacao_base = alt.Chart(df_adaptacao_militares)
adaptacao_chart = adaptacao_base.mark_bar(
    size=20).encode(
    x=alt.X('trigrama:N',
            sort=alt.EncodingSortField(field='dias_para_desadaptar',
                                        op='sum',
                                        order='descending'),
            axis=alt.Axis(title='',
                          labelAngle=0,
                          labelFontSize=16,
                          ticks=False,
                          labelColor='#747575',
                          labelAlign='center')),
    y=alt.Y('dias_sem_voar:Q', axis=alt.Axis(labels=False, title='')),
    color=alt.Color('funcao_a_bordo:N',
                    legend=alt.Legend(orient='top',
                                      title='',
                                      padding=20)),
)

adaptacao_chart_max_sem_voar = adaptacao_base.mark_bar(
    opacity=0.2,
    color='grey',
    size=20
).encode(
    x=alt.X('trigrama:N',
            sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending')),
    y=alt.Y('dias_para_desadaptar:Q'))

rotulo_dias_restantes = adaptacao_base.mark_text(
    color='#747575',
    baseline='top',
    fontSize=16,
    dy=-20
).encode(
    x=alt.X('trigrama:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending')),
    y=alt.Y('dias_sem_voar:Q'),
    text='label:N',
)

grafico_adaptacao = (adaptacao_chart_max_sem_voar + adaptacao_chart + rotulo_dias_restantes)
st.altair_chart(grafico_adaptacao, use_container_width=True)
