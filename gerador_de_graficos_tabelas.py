import pau_de_sebo
import altair as alt
import adaptacao
import time_handler
import pandas as pd
import esforco_aereo


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


def checar_adaptacao(x):
    if x >= 0:
        return x
    else:
        return 'Des.'


def gerar_grafico_pau_de_sebo(detalhes_tripulantes_df,
                              meta_pilotos_df,
                              dados_pessoais_df):

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
                sort=alt.EncodingSortField(field='Total_minutos',
                                           op='sum',
                                           order='descending'),
                axis=alt.Axis(title='',
                              labelAngle=-0,
                              labelFontSize=16,
                              ticks=False),
                ),
        y=alt.Y('value:Q', axis=alt.Axis(title='',
                                         labels=False)),
        color=alt.Color(
            'Categoria:N',
            scale=alt.Scale(domain=['LSP', 'RSP'],
                            range=['#194d82', '#148212']),
            legend=alt.Legend(title='Posição a Bordo',
                              orient='top')
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

    pau_de_sebo_dados = pau_de_sebo_df.drop(columns=['LSP',
                                                     'RSP',
                                                     'total_fake']).set_index('tripulante')

    grafico_pau_de_sebo = metas + graph + texto
    return grafico_pau_de_sebo, pau_de_sebo_dados


def gerar_grafico_adaptacao(detalhes_tripulantes_df,
                            dados_pessoais_df):
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

    adaptacao_base = alt.Chart(adaptacao_pilotos)
    adaptacao_chart = adaptacao_base.mark_bar(
        size=20).encode(
        x=alt.X('tripulante:N',
                sort=alt.EncodingSortField(field='dias_para_desadaptar',
                                           op='sum',
                                           order='descending'),
                axis=alt.Axis(title='',
                              labelAngle=0,
                              labelFontSize=16,
                              ticks=False,
                              labelColor='#747575',
                              labelAlign='center')),
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
        size=20
    ).encode(
        x=alt.X('tripulante:N',
                sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending')),
        y=alt.Y('dias_para_desadaptar:Q'))

    rotulo_dias_restantes = adaptacao_base.mark_text(
        color='#747575',
        baseline='top',
        fontSize=16,
        dy=-20
    ).encode(
        x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending')),
        y=alt.Y('dias_sem_voar_grafico:Q'),
        text='label_dias_restantes:N',
    )

    grafico_adaptacao = (adaptacao_chart_max_sem_voar + adaptacao_chart + rotulo_dias_restantes)
    return grafico_adaptacao, adaptacao_df_tabela_pintada


def gerar_grafico_adaptacao_impressao(detalhes_tripulantes_df,
                                      dados_pessoais_df):
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

    adaptacao_base = alt.Chart(adaptacao_pilotos)
    adaptacao_chart = adaptacao_base.mark_bar(
        size=20,
        dy=-17
    ).encode(
        x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending'),
                axis=alt.Axis(title='',
                              labelAngle=0,
                              labelFontSize=14,
                              labelPadding=10,
                              ticks=False,
                              labelColor='#747575',
                              grid=False)),
        y=alt.Y('dias_sem_voar_grafico:Q', axis=alt.Axis(labels=False,
                                                         title='',
                                                         grid=False)),
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
        size=20
    ).encode(
        x=alt.X('tripulante:N',
                sort=alt.EncodingSortField(field='dias_para_desadaptar',
                                           op='sum',
                                           order='descending'),
                axis=alt.Axis(labelFontSize=14,
                              labelAlign='center')),
        y=alt.Y('dias_para_desadaptar:Q')
    )

    rotulo_dias_restantes = adaptacao_base.mark_text(
        color='#242B2B',
        baseline='top',
        fontSize=14,
        dy=-17
    ).encode(
        x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending')),
        y=alt.Y('dias_sem_voar_grafico:Q'),
        text='label_dias_restantes:N',
    )

    grafico_adaptacao = (adaptacao_chart_max_sem_voar + adaptacao_chart + rotulo_dias_restantes)
    return grafico_adaptacao, adaptacao_df_tabela_pintada


def gerar_grafico_pau_de_sebo_impressao(detalhes_tripulantes_df,
                                        meta_pilotos_df,
                                        dados_pessoais_df):

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
                axis=alt.Axis(labelAngle=-0,
                              labelFontSize=14,
                              title='',
                              ticks=False,
                              labelPadding=10,
                              labelColor='#747575',
                              grid=False),
                ),
        y=alt.Y('value:Q', axis=alt.Axis(title='',
                                         labels=False,
                                         grid=False)),
        color=alt.Color(
            'Categoria:N',
            scale=alt.Scale(domain=['LSP', 'RSP'],
                            range=['#194d82', '#148212']),
            legend=alt.Legend(title='Posição a Bordo',
                              orient='top')
        ),
        tooltip=[
            alt.Tooltip('tripulante:N', title='Trig: '),
            alt.Tooltip('Total:N', title='Horas Totais: '),
            alt.Tooltip('LSP_label:N', title='LSP: '),
            alt.Tooltip('RSP_label:N', title='RSP: '),
        ]
    )

    texto = base.mark_text(
        fontSize=12,
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

    pau_de_sebo_dados = pau_de_sebo_df.drop(columns=['LSP',
                                                     'RSP',
                                                     'total_fake']).set_index('tripulante')

    grafico_pau_de_sebo = metas + graph + texto
    return grafico_pau_de_sebo, pau_de_sebo_dados


def gerar_grafico_demais_funcoes_impressao(funcao,
                                           funcoes_agrupadas,
                                           lista_funcoes_alunos,
                                           detalhes_tripulantes_df,
                                           meta_pilotos_df,
                                           dados_pessoais_df):
    pau_de_sebo_df = pau_de_sebo.pau_de_sebo(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                             meta_pilotos_df=meta_pilotos_df,
                                             dados_pessoais_df=dados_pessoais_df)[1]

    if funcao == 'Oficiais':
        pau_de_sebo_filtrado = pau_de_sebo_df.loc[(pau_de_sebo_df['funcao_a_bordo'].isin(
            funcoes_agrupadas.get(funcao))) | (pau_de_sebo_df['tripulante'] == 'DED')]
    else:
        pau_de_sebo_filtrado = pau_de_sebo_df.loc[pau_de_sebo_df['funcao_a_bordo'].isin(
            funcoes_agrupadas.get(funcao))]

    pau_de_sebo_sem_alunos = pau_de_sebo_filtrado.drop(
        pau_de_sebo_filtrado[pau_de_sebo_filtrado['funcao_a_bordo'].isin(lista_funcoes_alunos)].index)
    # alunos = pau_de_sebo_filtrado.loc[pau_de_sebo_filtrado['funcao_a_bordo'].isin(
    #     lista_funcoes_alunos), 'tripulante'].to_list()

    pau_de_sebo_sem_alunos = pau_de_sebo_sem_alunos.groupby(by='tripulante')[
        ['tempo_de_voo_minutos']].sum().reset_index()
    meta_horas = pau_de_sebo_sem_alunos['tempo_de_voo_minutos'].mean() * 0.75
    meta_horas_formatado = time_handler.transform_minutes_to_duration_string(meta_horas)
    pau_de_sebo_filtrado = pau_de_sebo_filtrado.drop(columns='funcao_a_bordo')
    pau_de_sebo_filtrado = pau_de_sebo_filtrado.groupby(by='tripulante')[['tempo_de_voo_minutos']].sum().reset_index()
    pau_de_sebo_filtrado['Tempo de Voo'] = pau_de_sebo_filtrado['tempo_de_voo_minutos'].map(
        time_handler.transform_minutes_to_duration_string)
    pau_de_sebo_filtrado = pau_de_sebo_filtrado.sort_values('tripulante', ascending=False)

    pau_de_sebo_chart_base = alt.Chart(pau_de_sebo_filtrado)
    pau_de_sebo_chart = pau_de_sebo_chart_base.mark_bar(
        size=20,
        color="#194d82"
    ).encode(
        x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='tempo_de_voo_minutos', op='sum', order='descending'),
                axis=alt.Axis(title='',
                              labelFontSize=12,
                              labelAngle=0,
                              labelPadding=10,
                              labelColor='#747575')),
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
        fontSize=10,
        dy=-10,
        color='#242B2B'
    ).encode(
        x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='tempo_de_voo_minutos', op='sum', order='descending'),
                axis=alt.Axis(title='', labelFontSize=18, labelAngle=0)),
        y=alt.Y('tempo_de_voo_minutos:Q'),
        text='Tempo de Voo:N'
    )

    return (meta_line + pau_de_sebo_chart + rotulo_horas_voadas), pau_de_sebo_filtrado, meta_horas_formatado


def gerar_grafico_demais_funcoes(funcao,
                                 funcoes_agrupadas,
                                 lista_funcoes_alunos,
                                 detalhes_tripulantes_df,
                                 meta_pilotos_df,
                                 dados_pessoais_df):
    pau_de_sebo_df = pau_de_sebo.pau_de_sebo(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                             meta_pilotos_df=meta_pilotos_df,
                                             dados_pessoais_df=dados_pessoais_df)[1]


    if funcao == 'Oficiais':
        pau_de_sebo_filtrado = pau_de_sebo_df.loc[(pau_de_sebo_df['funcao_a_bordo'].isin(
            funcoes_agrupadas.get(funcao))) | (pau_de_sebo_df['tripulante'] == 'DED')]
    else:
        pau_de_sebo_filtrado = pau_de_sebo_df.loc[pau_de_sebo_df['funcao_a_bordo'].isin(
            funcoes_agrupadas.get(funcao))]

    pau_de_sebo_sem_alunos = pau_de_sebo_filtrado.drop(
        pau_de_sebo_filtrado[pau_de_sebo_filtrado['funcao_a_bordo'].isin(lista_funcoes_alunos)].index)
    # alunos = pau_de_sebo_filtrado.loc[pau_de_sebo_filtrado['funcao_a_bordo'].isin(
    #     lista_funcoes_alunos), 'tripulante'].to_list()

    pau_de_sebo_sem_alunos = pau_de_sebo_sem_alunos.groupby(by='tripulante')[
        ['tempo_de_voo_minutos']].sum().reset_index()
    meta_horas = pau_de_sebo_sem_alunos['tempo_de_voo_minutos'].mean() * 0.75
    meta_horas_formatado = time_handler.transform_minutes_to_duration_string(meta_horas)
    pau_de_sebo_filtrado = pau_de_sebo_filtrado.drop(columns='funcao_a_bordo')
    pau_de_sebo_filtrado = pau_de_sebo_filtrado.groupby(by='tripulante')[['tempo_de_voo_minutos']].sum().reset_index()
    pau_de_sebo_filtrado['Tempo de Voo'] = pau_de_sebo_filtrado['tempo_de_voo_minutos'].map(
        time_handler.transform_minutes_to_duration_string)
    pau_de_sebo_filtrado = pau_de_sebo_filtrado.sort_values('tripulante', ascending=False)

    pau_de_sebo_chart_base = alt.Chart(pau_de_sebo_filtrado)
    pau_de_sebo_chart = pau_de_sebo_chart_base.mark_bar(
        size=30,
        color="#194d82"
    ).encode(
        x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='tempo_de_voo_minutos', op='sum', order='descending'),
                axis=alt.Axis(title='', labelFontSize=18, labelAngle=0, labelPadding=10, labelColor='#747575')),
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
        fontSize=16,
        dy=-10,
        color='#242B2B'
    ).encode(
        x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='tempo_de_voo_minutos', op='sum', order='descending'),
                axis=alt.Axis(title='', labelFontSize=18, labelAngle=0)),
        y=alt.Y('tempo_de_voo_minutos:Q'),
        text='Tempo de Voo:N'
    )

    return (meta_line + pau_de_sebo_chart + rotulo_horas_voadas), pau_de_sebo_filtrado, meta_horas_formatado


def gerar_grafico_adaptacao_demais_funcoes(funcao,
                                           funcoes_agrupadas,
                                           detalhes_tripulantes_df,
                                           dados_pessoais_df):
    adaptacao_tripulantes_df = adaptacao.gerar_adaptacao(detalhes_tripulantes_df=detalhes_tripulantes_df,
                                                         dados_pessoais_df=dados_pessoais_df)[1]

    adaptacao_tripulantes_df = adaptacao_tripulantes_df.loc[
        adaptacao_tripulantes_df['funcao_a_bordo'].isin(funcoes_agrupadas.get(funcao))]
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
        size=20
    ).encode(
        x=alt.X('tripulante:N', sort=alt.EncodingSortField(field='dias_para_desadaptar', op='sum', order='descending'),
                axis=alt.Axis(title='',
                              labelAngle=0,
                              labelFontSize=16,
                              ticks=False,
                              labelAlign='center', grid=False)),
        y=alt.Y('dias_sem_voar:Q', axis=alt.Axis(labels=False, title='')),
        color=alt.Color('funcao_a_bordo:N',
                        legend=alt.Legend(orient='top',
                                          title='Qualificação Operacional'),
                        scale=alt.Scale(domain=[i for i in funcoes_agrupadas.get(funcao)],
                                        range=['#194d82', '#148212', '#b56d00'])),
        tooltip=[alt.Tooltip('tripulante:N', title='Trig: '),
                 alt.Tooltip('data_voo:N', title='Último voo: '),
                 alt.Tooltip('voar_ate:N', title='Voar até: ')]
    )

    adaptacao_chart_max_sem_voar = adaptacao_tripulantes_base.mark_bar(
        opacity=0.2,
        color='grey',
        size=20
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

    return (adaptacao_chart_max_sem_voar + adaptacao_tripulantes_chart + rotulo_dias_restantes),\
        adaptacao_df_tabela_tripulantes_pintada, adaptacao_df_tabela_tripulantes


def gerar_grafico_esforco_aereo_impressao(aeronave,
                                          grupo,
                                          esforco_aereo_df):
    esforco_aereo_data = esforco_aereo.tratando_dados_esforco(esforco_aereo_df)
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
        size=20
    ).encode(
        x=alt.X('esforco:N', axis=alt.Axis(labelFontSize=10,
                                           title="",
                                           labelLimit=100,
                                           labelAngle=-45,
                                           labelPadding=10
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
        fontSize=12,
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
        fontSize=12,
        align='center',
        dy=-7

    ).encode(
        y='posicao_horas_voadas:Q',
        text='horas_gastas:N',
        color=alt.condition(alt.datum['Horas voadas'] < 0,
                            alt.value('#005202'),
                            alt.value('#005202')),
    )

    return esforco_chart + rotulo_horas_alocadas + rotulo_horas_voadas
