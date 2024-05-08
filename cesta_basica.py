import pandas as pd


def pintar_celulas_pr_np(val):
    if val >= 3:
        background_color = 'rgba(0, 266, 0, 0.2)'
        text_color = 'rgba(0, 149, 16, 1)'
    elif val >= 1:
        background_color = 'rgba(255, 255, 0, 0.4)'
        text_color = 'black'
    else:
        background_color = 'rgba(255, 0, 0, 0.25)'
        text_color = 'rgba(255, 0, 0, 1)'
    return f'background-color: {background_color}; color: {text_color}'


def pintar_celulas_arr_not_ifr(val):
    if val >= 1:
        background_color = 'rgba(0, 266, 0, 0.2)'
        text_color = 'rgba(0, 149, 16, 1)'
    else:
        background_color = 'rgba(255, 0, 0, 0.25)'
        text_color = 'rgba(255, 0, 0, 1)'
    return f'background-color: {background_color}; color: {text_color}; text-align: center; display: inline-block'


def gerar_cesta_basica(trimestre,
                       detalhes_tripulantes_df,
                       descidas_df,
                       dados_pessoais_df):
    lista_meses_do_trimestre = []
    for i in range(1, 13):
        if (i + 2) // 3 == trimestre:
            lista_meses_do_trimestre.append(i)
    detalhes_trip = detalhes_tripulantes_df
    lista_trigramas = dados_pessoais_df.loc[dados_pessoais_df['sigla_funcao'].str.contains('PIL',
                                                                                           case=False), 'trigrama']
    detalhes_trip_filtrada = detalhes_trip.loc[(detalhes_trip['funcao_a_bordo'] == '1P') |
                                               (detalhes_trip['funcao_a_bordo'] == 'IN') |
                                               ((detalhes_trip['funcao_a_bordo'] == 'AL') &
                                               (detalhes_trip['posicao_a_bordo'] == 'LSP'))]

    detalhes_trip_filtrada.loc[:, 'mes_voo'] = pd.to_datetime(detalhes_trip_filtrada['data_voo'],
                                                              format="%d/%m/%Y").dt.month
    detalhes_trip_filtrada = detalhes_trip_filtrada.loc[detalhes_trip_filtrada['mes_voo'].isin(
        lista_meses_do_trimestre)]
    detalhes_trip_filtrada = detalhes_trip_filtrada.rename(columns={'tempo_noturno': 'Noturno',
                                                                    'ifr_sem_pa': 'IFR sem PA',
                                                                    'arremetidas': 'Arremetidas',
                                                                    'tripulante': 'Tripulante'})

    if detalhes_trip_filtrada.empty:
        cesta_basica_zerados = pd.DataFrame({
            'Tripulante': lista_trigramas,
            'Arremetidas': 0,
            'IFR sem PA': 0,
            'Noturno': 0,
            'Precisão': 0,
            'Não Precisão': 0
        }).set_index('Tripulante')
        cesta_basica_pintada = cesta_basica_zerados.style.applymap(pintar_celulas_pr_np,
                                                                   subset=['Precisão',
                                                                           'Não Precisão']).applymap(
            pintar_celulas_arr_not_ifr,
            subset=['Arremetidas',
                    'IFR sem PA',
                    'Noturno'])

        return cesta_basica_pintada

    # Criando Colunas da tabela final
    trigramas = []
    quantidades = []
    tipo_procedimentos = []

    lista_id_voos = detalhes_tripulantes_df['IdVoo'].unique()
    voos_sem_descida = descidas_df[~descidas_df['IdVoo'].isin(lista_id_voos)]

    for i, row_tripulantes in detalhes_trip_filtrada.iterrows():
        id_voo = row_tripulantes['IdVoo']
        trigrama = row_tripulantes['Tripulante']
        descidas_filtrada = descidas_df[descidas_df['IdVoo'] == id_voo]

        for k, row_nao_descida in voos_sem_descida.iterrows():
            trigramas.append(trigrama)
            quantidades.append(0)
            tipo_procedimentos.append('')

        for j, row_descida in descidas_filtrada.iterrows():
            trigramas.append(trigrama)
            quantidades.append(row_descida['quantidade'])
            tipo_procedimentos.append(row_descida['tipo_procedimento'])

    df_final = pd.DataFrame({
        'Tripulante': trigramas,
        'quantidades': quantidades,
        'tipo de procedimento': tipo_procedimentos,
    })

    df_final['Precisão'] = df_final['tipo de procedimento'].map(lambda x: 0 if x else 1) * df_final['quantidades']
    df_final['Não Precisão'] = df_final['tipo de procedimento'].map(lambda x: 1 if x else 0) * df_final['quantidades']
    df_final.drop(columns=['quantidades', 'tipo de procedimento'], inplace=True)
    df_final = df_final.groupby(by='Tripulante')[['Precisão', 'Não Precisão']].sum().round(0).astype(int)
    detalhes_trip_filtrada.loc[:, 'Noturno'] = detalhes_trip_filtrada['Noturno'].apply(
        lambda x: 0 if str(x) == "00:00" else 1)

    cesta_basica_tripulantes = detalhes_trip_filtrada.groupby(by='Tripulante', as_index=False)[['Arremetidas',
                                                                                                'IFR sem PA',
                                                                                                'Noturno']].sum()
    cesta_basica_tripulantes['Arremetidas'] = cesta_basica_tripulantes['Arremetidas'].round(0).astype(int)
    cesta_basica_tripulantes['IFR sem PA'] = cesta_basica_tripulantes['IFR sem PA'].round(0).astype(int)
    cesta_basica_tripulantes['Noturno'] = cesta_basica_tripulantes['Noturno'].round(0).astype(int)

    # Adicionando tripulantes que estão zerados na cesta básica

    cesta_basica = pd.merge(cesta_basica_tripulantes, df_final, on='Tripulante')

    cesta_basica_zerados = pd.DataFrame({
        'Tripulante': list(set(lista_trigramas) - set(cesta_basica['Tripulante'])),
        'Arremetidas': 0,
        'IFR sem PA': 0,
        'Noturno': 0,
        'Precisão': 0,
        'Não Precisão': 0
    })

    cesta_basica_completa = pd.concat([cesta_basica, cesta_basica_zerados], ignore_index=True).set_index('Tripulante')

    cesta_basica_pintada = cesta_basica_completa.style.applymap(pintar_celulas_pr_np,
                                                                subset=['Precisão',
                                                                        'Não Precisão']).applymap(
        pintar_celulas_arr_not_ifr,
        subset=['Arremetidas',
                'IFR sem PA',
                'Noturno'])

    return cesta_basica_pintada
