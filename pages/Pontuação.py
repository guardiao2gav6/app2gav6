import streamlit as st
import adaptacao
from dados_gsheets import Dados, DadosMissoesFora
import time_handler
import altair as alt
from missoes_fora_de_sede_service import gerar_tabela_dias_fora
import pau_de_sebo


def generate_pontos_grafico(chart_base):

    pontos_voo_em_sede_base_chart = alt.Chart(chart_base)
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

    return pontos_voo_em_sede_chart + rotulo_pontos_voos_em_sede


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


def calcular_pontos_dias_fora(row):

    criterio_dias_fora_de_sede = {
        'Dias': [media_dias_fora * 0.75,
                 media_dias_fora * 0.15,
                 media_dias_fora * 0.95,
                 media_dias_fora * 1.05,
                 media_dias_fora * 1.15,
                 media_dias_fora * 1.25],
        'Pontuacao Dias fora de sede': [30, 25, 15, 10, 5, 0]
    }

    dias_fora_piloto = row['dias_comiss']

    medias = criterio_dias_fora_de_sede['Dias']
    pontos = criterio_dias_fora_de_sede['Pontuacao Dias fora de sede']
    pontuacao_dias_fora_piloto = 0
    for media in medias:
        if dias_fora_piloto <= media:
            indice = medias.index(media)
            pontuacao_dias_fora_piloto = pontos[indice]
            break
        else:
            pontuacao_dias_fora_piloto = 0

    row['Pontos Dias Fora'] = pontuacao_dias_fora_piloto
    row['Média dias fora'] = media_dias_fora
    return row


dados = Dados()
dados_comiss = DadosMissoesFora()
comiss_df = dados_comiss.get_comissionamentos()
detalhes_tripulantes_df = dados.generate_detalhes_tripulantes_df()
meta_pilotos_df = dados.generate_meta_pilotos_df()
dados_pessoais_df = dados.get_dados_pessoais()
descidas_df = dados.get_descidas()
aeronaves_df = dados.get_aeronaves()
esforco_aereo_df = dados.get_esforco_aereo()

pilotos = dados_pessoais_df.loc[dados_pessoais_df['sigla_funcao'].str.contains('PIL'), 'trigrama']
dias_fora_df = gerar_tabela_dias_fora(comiss_df)
dias_fora_df = dias_fora_df.rename(columns={'TRIGRAMA': 'tripulante'})
dias_fora_df = dias_fora_df.loc[dias_fora_df['tripulante'].isin(pilotos)]
dias_fora_df = dias_fora_df.groupby('tripulante')[['dias_comiss']].sum().reset_index()

adaptacao_df = adaptacao.gerar_adaptacao(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                         dados_pessoais_df=dados_pessoais_df)[0]
pau_de_sebo_df = pau_de_sebo.pau_de_sebo_pilotos(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                                 meta_pilotos_df=meta_pilotos_df,
                                                 dados_pessoais_df=dados_pessoais_df)
qtde_pilotos = pau_de_sebo_df.shape[0]
media_horas_pilotos = int(pau_de_sebo_df['Total_minutos'].sum() / qtde_pilotos)
media_dias_fora = int(dias_fora_df['dias_comiss'].sum() / qtde_pilotos)

df_pontuacao = {
    'Tripulante': [],
    'Horas totais': [],
    'Média esq': [],
    'Pontos Horas': [],
    'Dias desadapte': [],
    'Pontos desadapte': [],
    'Dias fora': [],
    'Pontos dias fora': [],
}

df_merged = pau_de_sebo_df.merge(adaptacao_df, on='tripulante')
df_merged = df_merged.merge(dias_fora_df, on='tripulante', how='outer')
df_merged['dias_comiss'] = df_merged['dias_comiss'].fillna(0)

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
                                    'dias_sem_voar_grafico',
                                    'LSP',
                                    'RSP'
                                    ])
df_merged = df_merged.rename(columns={
    'tripulante': 'Trigrama',
    'Total': 'Horas Totais',
    'label_dias_restantes': 'Dias para desadaptar'
})

df_merged['media_esq_minutos'] = media_horas_pilotos
df_merged['Média Horas Esq'] = time_handler.transform_minutes_to_duration_string(media_horas_pilotos)
df_merged['Pontos Horas'] = ''
df_merged['Pontos Adaptação'] = ''

pilotos = dados_pessoais_df.loc[dados_pessoais_df['sigla_funcao'].str.contains('PIL'), 'trigrama']

df_merged2 = df_merged.apply(calcular_pontos_horas, axis=1)
df_merged2 = df_merged2.apply(calcular_pontos_adaptacao, axis=1)
df_merged2 = df_merged2.apply(calcular_pontos_dias_fora, axis=1)

st.markdown('#### Pontuação Voos em Sede')
df_voos_em_sede = df_merged2.copy()
df_voos_em_sede = df_voos_em_sede.drop(columns=['Pontos Dias Fora',
                                                'Média dias fora',
                                                'dias_comiss'])
df_voos_em_sede['Total Pontos'] = df_voos_em_sede['Pontos Horas'] + df_voos_em_sede['Pontos Adaptação']
df_voos_em_sede = df_voos_em_sede.sort_values('Total Pontos', ascending=False)
df_voos_em_sede = df_voos_em_sede.drop(columns=['Total_minutos',
                                                'media_esq_minutos'])
if st.checkbox(label='Mostrar tabela', key='voos_em_sede'):
    st.dataframe(df_voos_em_sede)

grafico_voos_em_sede = generate_pontos_grafico(df_voos_em_sede)
st.altair_chart(grafico_voos_em_sede, use_container_width=True)

st.markdown('#### Sobreaviso CAV / R-99')
st.write('Para o cômputo dos pontos para sobreaviso CAV e R-99 ainda está faltando computador os quadrinhos,'
         'neste gráfico está sendo computado apenas horas, adaptaçao e dias fora de sede apenas para os comissionados,'
         'estou aguardando a SAP fazer a planilha de dias fora de sede para diaristas')
df_sobreaviso_cav = df_merged2.copy()

df_sobreaviso_cav['Total Pontos'] = df_sobreaviso_cav['Pontos Horas'] + \
                                    df_sobreaviso_cav['Pontos Adaptação'] + \
                                    df_sobreaviso_cav['Pontos Dias Fora']
df_sobreaviso_cav = df_sobreaviso_cav.sort_values('Total Pontos', ascending=False)
df_sobreaviso_cav = df_sobreaviso_cav.drop(columns=['Total_minutos',
                                                    'media_esq_minutos'])
df_sobreaviso_cav = df_sobreaviso_cav.reset_index(drop=True)

grafico_sobreaviso_cav = generate_pontos_grafico(df_sobreaviso_cav)

if st.checkbox(label='Mostrar tabela', key='sobreaviso'):
    st.dataframe(df_sobreaviso_cav)
st.altair_chart(grafico_sobreaviso_cav, use_container_width=True)
