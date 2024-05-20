import altair as alt
import time_handler


def gerar_posicao_texto(row):
    if row['horas_alocadas_minutos'] > 0 and row['horas_gastas_minutos'] <= row['horas_alocadas_minutos']:
        text_position = row['horas_alocadas_minutos']
    else:
        text_position = row['saldo_horas_minutos']
    return text_position


def tratando_dados_esforco(esforco_aereo_data):
    esforco_aereo_data_new = esforco_aereo_data.copy()

    horas_gastas_sesqae_sop = esforco_aereo_data_new.loc[(esforco_aereo_data_new['esforco'] == 'SESQAE (*)'),
                                                         ['aeronave', 'horas_gastas_minutos']]

    horas_gastas_sesqae_sop_r99 = horas_gastas_sesqae_sop.loc[horas_gastas_sesqae_sop['aeronave'] == 'R-99',
                                                              'horas_gastas_minutos'].iloc[0]
    horas_gastas_sesqae_sop_e99 = horas_gastas_sesqae_sop.loc[horas_gastas_sesqae_sop['aeronave'] == 'E-99',
                                                              'horas_gastas_minutos'].iloc[0]

    esforco_aereo_data_new.loc[(esforco_aereo_data_new['aeronave'] == 'R-99') &
                               (esforco_aereo_data_new['esforco'] == 'SESQAE'), 'horas_gastas_minutos'] += \
        horas_gastas_sesqae_sop_r99
    esforco_aereo_data_new.loc[(esforco_aereo_data_new['aeronave'] == 'E-99') &
                               (esforco_aereo_data_new['esforco'] == 'SESQAE'), 'horas_gastas_minutos'] +=\
        horas_gastas_sesqae_sop_e99
    esforco_aereo_data_new.loc[(esforco_aereo_data_new['aeronave'] == 'R-99') &
                               (esforco_aereo_data_new['esforco'] == 'SESQAE'), 'saldo_horas_minutos'] -= \
        horas_gastas_sesqae_sop_r99
    esforco_aereo_data_new.loc[(esforco_aereo_data_new['aeronave'] == 'E-99') &
                               (esforco_aereo_data_new['esforco'] == 'SESQAE'), 'saldo_horas_minutos'] -= \
        horas_gastas_sesqae_sop_e99

    esforco_aereo_data_new.loc[:, 'horas_gastas'] = esforco_aereo_data_new['horas_gastas_minutos'].map(
        time_handler.transform_minutes_to_duration_string)
    esforco_aereo_data_new.loc[:, 'saldo_horas'] = esforco_aereo_data_new['saldo_horas_minutos'].map(
        time_handler.transform_minutes_to_duration_string)
    esforco_aereo_data_new.loc[:, 'posicao_horas_voadas'] = 0
    esforco_aereo_data_new.loc[esforco_aereo_data_new['horas_gastas'] == '00:00', 'horas_gastas'] = ''

    mascara = esforco_aereo_data_new['esforco'] == 'SESQAE (*)'
    esforco_aereo_data_new = esforco_aereo_data_new.drop(esforco_aereo_data_new[mascara].index)

    esforco_aereo_data_new.loc[:, 'posicao_texto'] = esforco_aereo_data_new.apply(gerar_posicao_texto, axis=1)

    return esforco_aereo_data_new


def gerar_grafico_esforco(aeronave, grupo, esforco_aereo_df):
    esforco_aereo_data = tratando_dados_esforco(esforco_aereo_df)
    esforco_aereo_data = esforco_aereo_data.rename(columns={'saldo_horas_minutos': 'Saldo de Horas',
                                                            'horas_gastas_minutos': 'Horas voadas'})
    esforco_filtrado = esforco_aereo_data.loc[(esforco_aereo_data['aeronave'] == aeronave) &
                                              (esforco_aereo_data['grupo'] == grupo)]
    if esforco_filtrado['Saldo de Horas'].min() < 0:
        escala_minima_filtrado = esforco_filtrado['Saldo de Horas'].min()
    else:
        escala_minima_filtrado = 0

    base_esforco_filtrado = alt.Chart(esforco_filtrado, height=alt.Step(40)).transform_fold(
        ['Horas voadas',
         'Saldo de Horas'],
        as_=['variable', 'value']
    )

    esforco_chart = base_esforco_filtrado.mark_bar(
        width=30
    ).encode(
        x=alt.X('esforco:N', axis=alt.Axis(labelFontSize=14,
                                           title="",
                                           labelLimit=200,
                                           labelAngle=-90,
                                           ),
                sort=alt.EncodingSortField(field='Saldo de Horas', op='sum', order='descending')
                ),
        y=alt.Y('value:Q',
                axis=alt.Axis(title='',
                              labels=False),
                scale=alt.Scale(domainMin=escala_minima_filtrado)),
        order=alt.Order('horas_alocadas_minutos:N', sort='ascending'),
        color=alt.Color('variable:N',
                        scale=alt.Scale(domain=['Horas voadas',
                                                'Saldo de Horas'],
                                        range=['#9DEE9F',
                                               "rgba(0, 12, 105, .1)"]),
                        legend=alt.Legend(orient='top',
                                          title='',
                                          )),
        tooltip=[
            alt.Tooltip('esforco:N', title='Esforço: '),
            alt.Tooltip('horas_alocadas:N', title='Horas Alocadas: '),
            alt.Tooltip('horas_gastas:N', title='Horas Voadas: '),
            alt.Tooltip('saldo_horas:N', title='Saldo: ')
        ]
    )
    rotulo_horas_alocadas = esforco_chart.mark_text(
        fontSize=14,
        align='center',
        dy=alt.expr(alt.expr.if_(alt.datum['Saldo de Horas'] < 0, 15, -15))
    ).encode(
        y=alt.Y('posicao_texto:Q'),
        text='horas_alocadas:N',
        color=alt.condition(alt.datum['Saldo de Horas'] < 0,
                            alt.value('#c21328'),
                            alt.value('#696969')),
        tooltip=alt.value(None)

    )

    rotulo_horas_voadas = esforco_chart.mark_text(
        fontSize=14,
        align='center',
        dy=-7

    ).encode(
        y='posicao_horas_voadas:Q',
        text='horas_gastas:N',
        color=alt.condition(alt.datum['Horas voadas'] < 0,
                            alt.value('#005202'),
                            alt.value('#005202')),
    )

    return (esforco_chart + rotulo_horas_alocadas + rotulo_horas_voadas).properties(height=500)
