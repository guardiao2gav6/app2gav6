import datetime
import streamlit as st
import cesta_basica
import pau_de_sebo
import altair as alt
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
        return [''] * len(row)
    return [f'background-color: {background_color}; color: {text_color}'] * len(row)


# Carregando dados da página
dados = Dados()
detalhes_tripulantes_df = dados.generate_detalhes_tripulantes_df()
meta_pilotos_df = dados.generate_meta_pilotos_df()
dados_pessoais_df = dados.get_dados_pessoais()
descidas_df = dados.get_descidas()
aeronaves_df = dados.get_aeronaves()
esforco_aereo_df = dados.get_esforco_aereo()

# Pau de SEBO Pilotos
st.markdown("#### Pau de Sebo - Pilotos")
pau_de_sebo_df = pau_de_sebo.pau_de_sebo(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                         meta_pilotos_df=meta_pilotos_df,
                                         dados_pessoais_df=dados_pessoais_df)[0]
base = alt.Chart(pau_de_sebo_df).transform_fold(
    ['LSP', 'RSP'],
    as_=['Categoria', 'value']
)

graph = base.mark_bar(
    size=20
).encode(
    x=alt.X('tripulante:N',
            sort=alt.EncodingSortField(field='Total_minutos', op='sum', order='descending'),
            axis=alt.Axis(labelAngle=-0, labelFontSize=16, title='', ticks=False),
            ),
    y=alt.Y('value:Q', axis=alt.Axis(title='', labels=False)),
    color=alt.Color(
        'Categoria:N',
        scale=alt.Scale(domain=['LSP', 'RSP'], range=['#194d82', '#148212']),
        legend=alt.Legend(title='Posição a Bordo', orient='top')
    ),
    tooltip=[
        alt.Tooltip('tripulante:N', title='Trig: '),
        alt.Tooltip('Total:N', title='Horas Totais: '),
        alt.Tooltip('LSP_label:N', title='LSP: '),
        alt.Tooltip('RSP_label:N', title='RSP: '),
    ]
)

texto = base.mark_text(
    fontSize=16,
    dy=-20,
    color='#747575'
).encode(
    x=alt.X('tripulante:N',
            sort=alt.EncodingSortField(field='Total_minutos', op='sum', order='descending'),
            axis=alt.Axis(labelAngle=-0)
            ),
    y='mean(Total_minutos):Q',
    text='Total:N'
)

metas = base.mark_bar(
    opacity=0.08,
    size=20
).encode(
    x=alt.X('tripulante:N',
            sort=alt.EncodingSortField(field='Total_minutos', op='sum', order='descending'),
            axis=alt.Axis(labelAngle=-0)
            ),
    y=alt.Y('mean(meta_comprep_minutos):Q'),
    tooltip=[alt.Tooltip('tripulante:N', title='Trig: '),
             alt.Tooltip('meta_comprep:N', title='Meta COMPREP: '),
             alt.Tooltip('meta_esquadrao:N', title='Meta ESQ: ')]
)

if st.checkbox(label='Mostrar Dados - Pau de Sebo', key='pau_de_sebo_checkbox'):
    pau_de_sebo_dados = pau_de_sebo_df.drop(columns=['LSP',
                                                     'RSP',
                                                     'total_fake']).set_index('tripulante')
    st.dataframe(pau_de_sebo_dados.drop(columns=[
        'Total_minutos',
        'meta_comprep_minutos',
        'meta_esquadrao_minutos'
    ]))

grafico_pau_de_sebo = (metas + graph + texto)

st.altair_chart((metas + graph + texto), use_container_width=True)

# ADAPTAÇÃO
st.markdown('#### Adaptação Pilotos')
adaptacao_pilotos = adaptacao.gerar_adaptacao(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                              dados_pessoais_df=dados_pessoais_df)[0]

adaptacao_pilotos['data_voo'] = adaptacao_pilotos['data_voo'].map(lambda x: x.strftime("%d/%m/%Y"))
adaptacao_pilotos['voar_ate'] = adaptacao_pilotos['voar_ate'].map(lambda x: x.strftime("%d/%m/%Y"))

adaptacao_pilotos['Status'] = adaptacao_pilotos['dias_restantes'].map(analisar_status_adaptacao)
adaptacao_pilotos['Obs.'] = ''
adaptacao_pilotos.loc[adaptacao_pilotos['tripulante'].isin(['FUC',
                                                            'SBR',
                                                            'TAI',
                                                            'RPH']), 'Obs.'] = 'Curso fora de sede'
adaptacao_pilotos = adaptacao_pilotos.sort_values(by=['funcao_a_bordo', 'dias_sem_voar_grafico'], ascending=False)

adaptacao_df_tabela = adaptacao_pilotos.drop(columns=['dias_para_desadaptar',
                                                      'label_dias_restantes',
                                                      'dias_restantes',
                                                      'funcao_a_bordo',
                                                      'dias_sem_voar_grafico'])
adaptacao_df_tabela = adaptacao_df_tabela.rename(columns={'tripulante': 'Trig.',
                                                          'data_voo': 'Último Voo',
                                                          'voar_ate': 'Voar até',
                                                          'dias_sem_voar': 'Dias sem voar'})
adaptacao_df_tabela = adaptacao_df_tabela.sort_values(by=['Dias sem voar'], ascending=False)
adaptacao_df_tabela = adaptacao_df_tabela.set_index('Trig.')
adaptacao_df_tabela_pintada = adaptacao_df_tabela.style.apply(pintar_adaptacao, axis=1)

if st.checkbox(label='Mostrar Dados - Adaptação Pilotos'):
    st.dataframe(adaptacao_df_tabela_pintada, use_container_width=True)

adaptacao_base = alt.Chart(adaptacao_pilotos)
adaptacao_chart = adaptacao_base.mark_bar(
    size=25
).encode(
    x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending'),
            axis=alt.Axis(title='', labelAngle=0, labelFontSize=16, labelPadding=20, ticks=False)),
    y=alt.Y('dias_sem_voar_grafico:Q', axis=alt.Axis(labels=False, title='')),
    color=alt.Color('funcao_a_bordo:N',
                    legend=alt.Legend(orient='top',
                                      title='',
                                      padding=20),
                    scale=alt.Scale(domain=['IN', '1P', 'AL'],
                                    range=['#194d82', '#148212', '#b56d00'])),
    tooltip=[alt.Tooltip('tripulante:N', title='Trig: '),
             alt.Tooltip('data_voo:N', title='Último voo: '),
             alt.Tooltip('voar_ate:N', title='Voar até: ')]
)

adaptacao_chart_max_sem_voar = adaptacao_base.mark_bar(
    opacity=0.2,
    color='grey',
    size=25
).encode(
    x=alt.X('tripulante:N',
            sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending'),
            axis=alt.Axis(labelFontSize=16, labelAlign='center')),
    y=alt.Y('dias_para_desadaptar:Q')
)

rotulo_dias_restantes = adaptacao_base.mark_text(
    color='#747575',
    baseline='top',
    fontSize=16,
    dy=-25
).encode(
    x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending')),
    y=alt.Y('dias_sem_voar_grafico:Q'),
    text='label_dias_restantes:N',
)

grafico_adaptacao = (adaptacao_chart_max_sem_voar + adaptacao_chart + rotulo_dias_restantes)
st.altair_chart((adaptacao_chart_max_sem_voar + adaptacao_chart + rotulo_dias_restantes), use_container_width=True)

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
                                                         detalhes_tripulantes_df=detalhes_tripulantes_df,
                                                         descidas_df=descidas_df,
                                                         dados_pessoais_df=dados_pessoais_df)
st.dataframe(cesta_basica_trimestre, use_container_width=True)
