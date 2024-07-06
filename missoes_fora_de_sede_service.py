import pandas as pd
from dados_gsheets import DadosMissoesFora, Dados
import streamlit as st
import altair as alt
import datetime



def gerar_tabela_dias_fora(comiss_df):
    comiss_group_trigrama = comiss_df.groupby(by=['TRIGRAMA', "Status"]).agg(
        dias_comiss=('DIAS COMISS', 'sum'),
        Missoes=('NOME DA MISSÃO', lambda x: ' - '.join(x)),
    ).reset_index()

    teste_grouped = comiss_group_trigrama.groupby('TRIGRAMA')['dias_comiss'].sum().reset_index()
    comiss_group_trigrama = pd.merge(comiss_group_trigrama, teste_grouped, on='TRIGRAMA')
    comiss_group_trigrama = comiss_group_trigrama.rename(columns={'dias_comiss_x': 'dias_comiss',
                                                                  'dias_comiss_y': 'Total'})

    return comiss_group_trigrama


def gerar_grafico_dias_fora(comiss_df):
    comiss_group_trigrama = gerar_tabela_dias_fora(comiss_df)
    base = alt.Chart(comiss_group_trigrama)
    chart = base.mark_bar(
        size=10,
        color="#194d82"
    ).encode(
        x=alt.X('TRIGRAMA:N',
                sort=alt.EncodingSortField(field='Total',
                                           op='mean',
                                           order='descending'),
                axis=alt.Axis(title='',
                              labelAngle=0,
                              labelFontSize=12,
                              ticks=False,
                              labelColor='#747575',
                              labelAlign='center')),
        y=alt.Y('sum(dias_comiss):Q', axis=alt.Axis(labels=False, title='')),
        color=alt.Color(
            'Status:N',
            scale=alt.Scale(domain=['SIM', 'PREV'],
                            range=['#194d82', 'rgba(0, 100, 0, 0.3']),
            legend=alt.Legend(title='Status Missão',
                              orient='top')
        ),
        tooltip=[alt.Tooltip('TRIGRAMA:N', title='Trig: '),
                 alt.Tooltip('Missoes:N', title='Missões: ')]
    )

    rotulos_comiss = base.mark_text(
        color='#747575',
        baseline='top',
        fontSize=12,
        dy=-20
    ).encode(
        x=alt.X('TRIGRAMA:N', sort=alt.EncodingSortField(field='Total', op='mean', order='descending')),
        y=alt.Y('mean(Total):Q'),
        text='Total:N',
    )

    return chart + rotulos_comiss
