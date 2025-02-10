from dados_gsheets import Dados
import streamlit as st
import datetime
import altair as alt
import pandas as pd
import time_handler
from models.militar import Militar


def retirar_funcoes_nao_exercidas(horas_militares_filtrado_grupo, grupo):
  result = []
  for horas_militar in horas_militares_filtrado_grupo:
    if grupo == Militar.posicoes_a_bordo:
      horas_militar_filtrado = horas_militar['posicoes_a_bordo']
      
    else:
      horas_militar_filtrado = {chave: valor for chave, valor in horas_militar.items() if chave in grupo
    }

    totais_horas = sum(valor for chave, valor in horas_militar_filtrado.items())
    horas_militar_filtrado['Totais'] = totais_horas

    horas_militar_filtrado = {'trigrama': horas_militar['trigrama'],
    **horas_militar_filtrado,
    **{chave + '_hhmm': time_handler.transform_minutes_to_duration_string(valor) for chave, valor in horas_militar_filtrado.items() if chave != 'trigrama'}}
    result.append(horas_militar_filtrado)
  return result


def filtrando_militares_por_grupo(grupo, militares):
  if grupo == Militar.posicoes_a_bordo:
    militares_filtrados_por_grupo = [militar for militar in militares if 'PIL' in militar.sigla_funcao]
  else:
    militares_filtrados_por_grupo = list(filter(lambda x: bool(set(grupo) & set(x.funcoes_a_bordo)), militares))
  return militares_filtrados_por_grupo

# Carregando dados
dados = Dados()
aeronaves = dados.get_aeronaves()['modelo'].unique()
esforco_aereo = dados.get_esforco_aereo()['esforco'].unique()

# FILTROS
filtro_periodo = st.date_input(label='Período', value=[datetime.date(2025, 1, 1), datetime.date.today()], key='periodo')

filtro_aeronave = st.multiselect(label='Aeronave', options=aeronaves)
if not filtro_aeronave:
  filtro_aeronave = aeronaves

filtro_esforco_aereo = st.multiselect(label='Esforço Aéreo', options=esforco_aereo)
if not filtro_esforco_aereo:
  filtro_esforco_aereo = esforco_aereo

filtro_funcao_a_bordo = st.selectbox(label='Função à Bordo', options=Militar.funcoes_agrupadas.keys())

# Extraindo dados apenas do período selecionado
militares = dados.get_militares(filtro_periodo,
                                filtro_aeronave,
                                filtro_esforco_aereo)

# Lista de funções à bordo para cada grupo
grupo = Militar.funcoes_agrupadas[filtro_funcao_a_bordo]

militares_filtrados_por_grupo = filtrando_militares_por_grupo(grupo, militares)

horas_militares = list(map(lambda x: x.horas_militar, militares_filtrados_por_grupo))
horas_militares = retirar_funcoes_nao_exercidas(horas_militares,
grupo)

df_horas_militares = pd.DataFrame(horas_militares)
labels = [label for label in horas_militares[0].keys() if label not in grupo]
df_long = df_horas_militares.melt(id_vars=labels, value_vars=grupo, 
                   var_name='funcoes', value_name='horas')

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
  color=alt.Color('funcoes:N',
  scale=alt.Scale(domain=grupo,
  range=['#219ebc', '#023047', '#fb8500', '#1a8273']),
        legend=alt.Legend(title='Função/Posição à Bordo',
                            orient='top')),
                            tooltip=[
        alt.Tooltip('trigrama:N', title='Trig: '),
        *[alt.Tooltip(f'{label}:N', title=f'{label[:-5]}: ') for label in labels if label not in ['trigrama', 'Totais']],
    ]
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

adaptacao_militares = list(map(lambda x: x.adaptacao, militares_filtrados_por_grupo))

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
