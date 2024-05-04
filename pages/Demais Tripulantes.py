import pandas as pd
import streamlit as st
import pau_de_sebo
import altair as alt
import time_handler
import adaptacao
from dados_gsheets import Dados


def analisar_status_adaptacao(dias_restantes):
    if dias_restantes > 10:
        return 'ADAPTADO'
    elif dias_restantes >= 0:
        return f'{dias_restantes} dia(s) para DESADAPTAR'
    else:
        return 'DESADAPTADO'


def pintar_adaptacao(row):
    status_adaptacao = row['Status']
    if status_adaptacao == 'DESADAPTADO':
        background_color = 'rgba(255, 0, 0, 0.25)'
        text_color = 'rgba(255, 0, 0, 1)'
    elif 'para DESADAPTAR' in status_adaptacao:
        background_color = 'rgba(255, 255, 0, 0.4)'
        text_color = 'black'
    else:
        background_color = 'rgba(0, 266, 0, 0.2)'
        text_color = 'black'
    return [f'background-color: {background_color}; color: {text_color}'] * len(row)


def checar_adaptacao(x):
    if x >= 0:
        return x
    else:
        return 'Des.'


# CARREGANDO DADOS PARA PÁGINA
dados = Dados()
detalhes_tripulantes_df = dados.generate_detalhes_tripulantes_df()
meta_pilotos_df = dados.generate_meta_pilotos_df()
dados_pessoais_df = dados.get_dados_pessoais()

funcoes_agrupadas = {'Mecânicos': ['AC', 'MC', 'IC'],
                     'Chefe Controlador': ['AB-R', 'CC-R', 'IB-R'],
                     'COTAT': ['AJ', 'CT', 'IJ'],
                     'COAM': ['AD-R', 'CO-R', 'ID-R'],
                     'O3': ['A3', 'O3', 'I3'],
                     'O1': ['A1', 'O1', 'I1'],
                     'MA-R': ['AA-R', 'MA-R', 'IA-R'],
                     'MA-E': ['AA-E', 'MA-E', 'IA-E'],
                     'Oficiais': ['AB-R', 'CC-R', 'IB-R', 'AJ', 'CT', 'IJ', '1P', '2P', 'IN', 'AL']}

lista_funcoes_alunos = [i[0] for i in funcoes_agrupadas.values()]
filtro_funcoes = st.selectbox(label='Funções a Bordo', options=['Chefe Controlador',
                                                                'COTAT',
                                                                'Mecânicos',
                                                                'COAM',
                                                                'O1',
                                                                'O3',
                                                                'MA-E',
                                                                'MA-R',
                                                                'Oficiais'])

st.markdown(f'#### Pau de Sebo - {filtro_funcoes}.')

pau_de_sebo_df = pau_de_sebo.pau_de_sebo(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                         meta_pilotos_df=meta_pilotos_df,
                                         dados_pessoais_df=dados_pessoais_df)[1]

if filtro_funcoes == 'Oficiais':
    pau_de_sebo_filtrado = pau_de_sebo_df.loc[(pau_de_sebo_df['funcao_a_bordo'].isin(
        funcoes_agrupadas.get(filtro_funcoes))) | (pau_de_sebo_df['tripulante'] == 'DED')]
else:
    pau_de_sebo_filtrado = pau_de_sebo_df.loc[pau_de_sebo_df['funcao_a_bordo'].isin(
        funcoes_agrupadas.get(filtro_funcoes))]

pau_de_sebo_sem_alunos = pau_de_sebo_filtrado.drop(
    pau_de_sebo_filtrado[pau_de_sebo_filtrado['funcao_a_bordo'].isin(lista_funcoes_alunos)].index)

alunos = pau_de_sebo_filtrado.loc[pau_de_sebo_filtrado['funcao_a_bordo'].isin(
    lista_funcoes_alunos), 'tripulante'].to_list()

pau_de_sebo_sem_alunos = pau_de_sebo_sem_alunos.groupby(by='tripulante')[['tempo_de_voo_minutos']].sum().reset_index()
meta_horas = pau_de_sebo_sem_alunos['tempo_de_voo_minutos'].mean() * 0.75
meta_horas_formatado = time_handler.transform_minutes_to_duration_string(meta_horas)
pau_de_sebo_filtrado = pau_de_sebo_filtrado.drop(columns='funcao_a_bordo')
pau_de_sebo_filtrado = pau_de_sebo_filtrado.groupby(by='tripulante')[['tempo_de_voo_minutos']].sum().reset_index()
pau_de_sebo_filtrado['Tempo de Voo'] = pau_de_sebo_filtrado['tempo_de_voo_minutos'].map(
    time_handler.transform_minutes_to_duration_string)
pau_de_sebo_filtrado = pau_de_sebo_filtrado.sort_values('tripulante', ascending=False)

pau_de_sebo_chart_base = alt.Chart(pau_de_sebo_filtrado)
pau_de_sebo_chart = pau_de_sebo_chart_base.mark_bar(
    color="#194d82"
).encode(
    x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='tempo_de_voo_minutos', op='sum', order='descending'),
            axis=alt.Axis(title='', labelFontSize=18, labelAngle=0)),
    y=alt.Y('tempo_de_voo_minutos:Q', axis=alt.Axis(title='', labels=False)),
    tooltip=[alt.Tooltip('tripulante:N', title='Trig: '),
             alt.Tooltip('Tempo de Voo:N', title='Horas voadas: ')]
)
meta_line = alt.Chart(pd.DataFrame({'y': [meta_horas]})).mark_rule(
    strokeDash=[10, 10],
    strokeWidth=2.5,
    color='#303030',
    strokeOpacity=0.3
).encode(
    y='y:Q'
)

rotulo_horas_voadas = pau_de_sebo_chart_base.mark_text(
    fontSize=18,
    dy=-20,
    color='#747575'
).encode(
    x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='tempo_de_voo_minutos', op='sum', order='descending'),
            axis=alt.Axis(title='', labelFontSize=18, labelAngle=0)),
    y=alt.Y('tempo_de_voo_minutos:Q'),
    text='Tempo de Voo:N'
)

if st.checkbox(label='Mostrar Dados'):
    st.dataframe(pau_de_sebo_filtrado.drop(columns=['tempo_de_voo_minutos']).set_index('tripulante'))


st.altair_chart((pau_de_sebo_chart + meta_line + rotulo_horas_voadas).properties(title=alt.TitleParams(
    text=" ",
    subtitle=f'A linha tracejada representa 75% da média ({meta_horas_formatado}).',
    subtitleFontSize=16,
    fontSize=1,
    anchor='start'
)), use_container_width=True)

st.markdown('###### A meta de Horas de Voo para tripulantes cumprindo funções que não envolvem pilotagem.')
st.markdown('O intuito dessa meta não é atingir um mínimo de horas de voo e sim equalizar as horas entre os tripulantes'
            '. Por isso essa meta é dinâmica e obtida calculando-se 75% da média das horas voadas por cada tripulante.')
st.markdown('Ex: Se a média de horas voadas entre os tripulantes de determinado QT forem 100:00 a meta mínima para cada'
            ' tripulante desse QT será de 75% de 100 horas que é 75h. Ou seja, se algum tripulante estiver com as horas'
            ' muito discrepante dos demais ele fará com que a média suba e os demais fiquem abaixo da meta. Para que '
            'isso não ocorra, cada escalante deve sempre deixar as horas o mais equalizadas possível.')
st.markdown('*Alunos do ano corrente não entram neste cômputo*')


# Adaptação Tripulantes
st.markdown(f'#### Adaptação - {filtro_funcoes}')
adaptacao_tripulantes_df = adaptacao.gerar_adaptacao(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                                     dados_pessoais_df=dados_pessoais_df)[1]

adaptacao_tripulantes_df = adaptacao_tripulantes_df.loc[
    adaptacao_tripulantes_df['funcao_a_bordo'].isin(funcoes_agrupadas.get(filtro_funcoes))]
adaptacao_tripulantes_df = adaptacao_tripulantes_df.sort_values(by=['dias_para_desadaptar',
                                                                    'dias_sem_voar'],
                                                                ascending=False)
adaptacao_tripulantes_df['data_voo'] = adaptacao_tripulantes_df['data_voo'].map(lambda x: x.strftime("%d/%m/%Y"))
adaptacao_tripulantes_df['voar_ate'] = adaptacao_tripulantes_df['voar_ate'].map(lambda x: x.strftime("%d/%m/%Y"))
adaptacao_tripulantes_df['label_dias_restantes'] = adaptacao_tripulantes_df['dias_restantes'].map(checar_adaptacao)
adaptacao_tripulantes_df['Status'] = adaptacao_tripulantes_df['dias_restantes'].map(analisar_status_adaptacao)
adaptacao_tripulantes_df = adaptacao_tripulantes_df.sort_values(by=['dias_restantes'], ascending=True)
adaptacao_df_tabela_tripulantes = adaptacao_tripulantes_df.drop(columns=['dias_para_desadaptar',
                                                                         'label_dias_restantes',
                                                                         'dias_restantes',
                                                                         'funcao_a_bordo'])
adaptacao_df_tabela_tripulantes = adaptacao_df_tabela_tripulantes.rename(columns={'tripulante': 'Trig.',
                                                                                  'data_voo': 'Último Voo',
                                                                                  'voar_ate': 'Voar até',
                                                                                  'dias_sem_voar': 'Dias sem voar'})
adaptacao_df_tabela_tripulantes = adaptacao_df_tabela_tripulantes.set_index('Trig.')
adaptacao_df_tabela_tripulantes_pintada = adaptacao_df_tabela_tripulantes.style.apply(pintar_adaptacao, axis=1)

adaptacao_tripulantes_base = alt.Chart(adaptacao_tripulantes_df)
adaptacao_tripulantes_chart = adaptacao_tripulantes_base.mark_bar(
    size=25
).encode(
    x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending'),
            axis=alt.Axis(title='', labelAngle=0, labelFontSize=16, labelPadding=20, ticks=False, labelAlign='center')),
    y=alt.Y('dias_sem_voar:Q', axis=alt.Axis(labels=False, title='')),
    color=alt.Color('funcao_a_bordo:N',
                    legend=alt.Legend(orient='top',
                                      title='Qualificação Operacional'),
                    scale=alt.Scale(domain=[i for i in funcoes_agrupadas.get(filtro_funcoes)],
                                    range=['#194d82', '#148212', '#b56d00'])),
    tooltip=[alt.Tooltip('tripulante:N', title='Trig: '),
             alt.Tooltip('data_voo:N', title='Último voo: '),
             alt.Tooltip('voar_ate:N', title='Voar até: ')]
)

adaptacao_chart_max_sem_voar = adaptacao_tripulantes_base.mark_bar(
    opacity=0.2,
    color='grey',
    size=25
).encode(
    x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending')),
    y=alt.Y('dias_para_desadaptar:Q'),
    tooltip=[alt.Tooltip('tripulante:N', title='Trig: '),
             alt.Tooltip('dias_para_desadaptar:Q', title='Dias para Desadaptar: ')]
)

rotulo_dias_restantes = adaptacao_tripulantes_base.mark_text(
    color='#747575',
    baseline='top',
    fontSize=16,
    dy=-25
).encode(
    x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending')),
    y=alt.Y('dias_sem_voar:Q'),
    text='label_dias_restantes:N',
    tooltip=alt.value(None)
)
# if st.checkbox(label=f'Mostrar Dados - Adaptação {filtro_funcoes}'):
col1, col_vazia, col2 = st.columns([0.45, 0.02, 0.53])
with col1:
    st.dataframe(adaptacao_df_tabela_tripulantes_pintada, use_container_width=True)
with col2:
    st.altair_chart((adaptacao_chart_max_sem_voar + adaptacao_tripulantes_chart + rotulo_dias_restantes),
                    use_container_width=True)

percentual_adaptado = adaptacao_df_tabela_tripulantes['Status'].value_counts().loc['ADAPTADO'] / adaptacao_tripulantes_df.shape[0]
if percentual_adaptado < 0.7:
    st.markdown(f'###### ATENÇÃO: {round((1 - percentual_adaptado) * 100, 2)}% do QT selecionado está DESADAPTADO')

st.markdown('- Os números escritos acima das barras representam a quantidade de dias restantes que o militar ainda pode'
            'ficar sem voar.')
st.markdown('- Por enquanto, esses dados levam em consideração apenas os voos realizados, sendo assim, o escalante de '
            'COAM deve ficar atento para possíveis readaptações em MPTS que não serão contabilizadas aqui.')
