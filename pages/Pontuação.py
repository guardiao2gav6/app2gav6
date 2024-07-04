import streamlit as st
import adaptacao
from dados_gsheets import Dados
import gerador_de_graficos_tabelas
import time_handler
import pandas as pd
import altair as alt


dados = Dados()
detalhes_tripulantes_df = dados.generate_detalhes_tripulantes_df()
meta_pilotos_df = dados.generate_meta_pilotos_df()
dados_pessoais_df = dados.get_dados_pessoais()
descidas_df = dados.get_descidas()
aeronaves_df = dados.get_aeronaves()
esforco_aereo_df = dados.get_esforco_aereo()

adaptacao_df = adaptacao.gerar_adaptacao(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                         dados_pessoais_df=dados_pessoais_df)[0]
pau_de_sebo_df = gerador_de_graficos_tabelas.gerar_grafico_pau_de_sebo(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                                                       meta_pilotos_df=meta_pilotos_df,
                                                                       dados_pessoais_df=dados_pessoais_df)[1]
pau_de_sebo_df = pau_de_sebo_df.reset_index()


qtde_pilotos = pau_de_sebo_df.shape[0]
media_horas_pilotos = int(pau_de_sebo_df['Total_minutos'].sum()/qtde_pilotos)

df_pontuacao = {
    'Tripulante': [],
    'Horas totais': [],
    'Média esq': [],
    'Pontos Horas': [],
    'Dias desadapte': [],
    'Pontos desadapte': []
}

df_merged = pd.merge(pau_de_sebo_df, adaptacao_df, on='tripulante')
df_merged = df_merged.drop(columns=['LSP_label',
                                    'RSP_label',
                                    'meta_esquadrao',
                                    'meta_comprep_minutos',
                                    'meta_esquadrao_minutos',
                                    'meta_comprep',
                                    'funcao_a_bordo',
                                    'dias_para_desadaptar',
                                    'data_voo',
                                    'voar_ate',
                                    'dias_restantes',
                                    'dias_sem_voar',
                                    'dias_sem_voar_grafico'])
df_merged = df_merged.rename(columns={
    'tripulante': 'Trigrama',
    'Total': 'Horas Totais',
    'label_dias_restantes': 'Dias para desadaptar'
})

df_merged['media_esq_minutos'] = media_horas_pilotos
df_merged['Média Horas Esq'] = time_handler.transform_minutes_to_duration_string(media_horas_pilotos)
df_merged['Pontos Horas'] = ''
df_merged['Pontos Adaptação'] = ''


def calcular_pontos_horas(row):

    criterio_horas_voo_em_sede = {
        'Horas': [media_horas_pilotos * 0.75,
                  media_horas_pilotos * 0.15,
                  media_horas_pilotos * 0.95,
                  media_horas_pilotos * 1.05,
                  media_horas_pilotos * 1.15,
                  media_horas_pilotos * 1.25],
        'Pontuacao Horas': [30, 25, 15, 10, 5, 0]
    }

    horas_piloto = row['Total_minutos']

    medias = criterio_horas_voo_em_sede['Horas']
    pontos = criterio_horas_voo_em_sede['Pontuacao Horas']
    pontuacao_piloto_horas = 0
    for media in medias:
        if horas_piloto <= media:
            indice = medias.index(media)
            pontuacao_piloto_horas = pontos[indice]
            break
        else:
            pontuacao_piloto_horas = 0

    row['Pontos Horas'] = pontuacao_piloto_horas
    return row
    # st.write(row['Pontos Horas'])


def calcular_pontos_adaptacao(row):

    criterio_adaptacao_voos_em_sede = {
        'adaptacao vence em': [1, 3, 5, 10, 15],
        'Pontuacao adaptação': [15, 12, 10, 8, 5, 0]
    }

    dias_restantes = row['Dias para desadaptar']
    parametros_adaptacao = criterio_adaptacao_voos_em_sede['adaptacao vence em']
    pontos_adaptacao = criterio_adaptacao_voos_em_sede['Pontuacao adaptação']
    pontuacao_piloto_adaptacao = 0
    if dias_restantes == 'Des.':
        pontuacao_piloto_adaptacao = 20
    else:
        for parametro in parametros_adaptacao:
            if dias_restantes <= parametro:
                indice = parametros_adaptacao.index(parametro)
                pontuacao_piloto_adaptacao = pontos_adaptacao[indice]
                break
            else:
                pontuacao_piloto_adaptacao = 0

    row['Pontos Adaptação'] = pontuacao_piloto_adaptacao
    return row


df_merged2 = df_merged.apply(calcular_pontos_horas, axis=1)
df_merged2 = df_merged2.apply(calcular_pontos_adaptacao, axis=1)
df_merged2['Total Pontos'] = df_merged2['Pontos Horas'] + df_merged2['Pontos Adaptação']
df_merged2 = df_merged2.sort_values('Total Pontos', ascending=False)
df_merged2 = df_merged2.drop(columns=['Total_minutos',
                                      'media_esq_minutos'])

st.markdown('#### Pontuação Voos em Sede')
if st.checkbox(label='Mostrar Tabela de Pontos'):
    st.dataframe(df_merged2)

pontos_voo_em_sede_base_chart = alt.Chart(df_merged2)
pontos_voo_em_sede_chart = pontos_voo_em_sede_base_chart.mark_bar(
        size=20).encode(
        x=alt.X('Trigrama:N',
                sort=alt.EncodingSortField(field='Total Pontos',
                                           op='sum',
                                           order='descending'),
                axis=alt.Axis(title='',
                              labelAngle=0,
                              labelFontSize=16,
                              ticks=False,
                              labelColor='#747575',
                              labelAlign='center')),
        y=alt.Y('Total Pontos:Q', axis=alt.Axis(labels=False, title='')))

rotulo_pontos_voos_em_sede = pontos_voo_em_sede_chart.mark_text(
    color='#747575',
    baseline='top',
    fontSize=16,
    dy=-20
).encode(
    x=alt.X('Trigrama:N', sort=alt.EncodingSortField(field='Total Pontos',
                                                     op='sum',
                                                     order='descending')),
    y=alt.Y('Total Pontos:Q'),
    text='Total Pontos:N',
)
st.altair_chart((pontos_voo_em_sede_chart + rotulo_pontos_voos_em_sede), use_container_width=True)
