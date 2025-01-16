import streamlit as st
import gerador_de_graficos_tabelas
import altair as alt
from dados_gsheets import Dados
import datetime


dados = Dados()
detalhes_tripulantes_df = dados.generate_detalhes_tripulantes_df()
meta_pilotos_df = dados.generate_meta_pilotos_df()
dados_pessoais_df = dados.get_dados_pessoais()
descidas_df = dados.get_descidas()
aeronaves_df = dados.get_aeronaves()
esforco_aereo_df = dados.get_esforco_aereo()


filtro_data_pau_sebo_tripulantes = st.date_input(label='Início - Término', value=[datetime.date(2025, 1, 1), datetime.date.today()])
detalhes_tripulantes_df_filtrada = detalhes_tripulantes_df.loc[(detalhes_tripulantes_df['data_voo'].dt.date)>=filtro_data_pau_sebo_tripulantes[0]]

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

pau_de_sebo_demais_funcoes_chart = gerador_de_graficos_tabelas.gerar_grafico_demais_funcoes(
    funcao=filtro_funcoes,
    funcoes_agrupadas=funcoes_agrupadas,
    lista_funcoes_alunos=lista_funcoes_alunos,
    detalhes_tripulantes_df=detalhes_tripulantes_df_filtrada,
    dados_pessoais_df=dados_pessoais_df)

if st.checkbox(label='Mostrar Dados'):
    st.dataframe(pau_de_sebo_demais_funcoes_chart[1].drop(columns=['tempo_de_voo_minutos']).set_index('tripulante'))


st.altair_chart(pau_de_sebo_demais_funcoes_chart[0].properties(title=alt.TitleParams(
    text=" ",
    subtitle=f'A linha tracejada representa 75% da média ({pau_de_sebo_demais_funcoes_chart[2]}).',
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
adaptacao_demais_funcoes_chart = gerador_de_graficos_tabelas.gerar_grafico_adaptacao_demais_funcoes(
    funcao=filtro_funcoes,
    funcoes_agrupadas=funcoes_agrupadas,
    detalhes_tripulantes_df=detalhes_tripulantes_df_filtrada,
    dados_pessoais_df=dados_pessoais_df
)

if st.checkbox(label=f'Mostrar Dados - Adaptação {filtro_funcoes}'):
    st.dataframe(adaptacao_demais_funcoes_chart[1], use_container_width=True)

st.altair_chart(adaptacao_demais_funcoes_chart[0], use_container_width=True)

percentual_adaptado = adaptacao_demais_funcoes_chart[2]['Status'].value_counts().loc['ADAPTADO'] / \
                      adaptacao_demais_funcoes_chart[2].shape[0]
if percentual_adaptado < 0.7:
    st.markdown(f'###### ATENÇÃO: {round((1 - percentual_adaptado) * 100, 2)}% do QT selecionado está DESADAPTADO')
