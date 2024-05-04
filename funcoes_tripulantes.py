import pandas as pd


def funcoes_tripulantes(dados_pessoais):
    funcoes_dos_tripulantes = dados_pessoais.loc[(dados_pessoais['funcoes_a_bordo'] != 'NIL') &
                                                 (dados_pessoais['sigla_funcao'] != 'NIL')]

    trigramas_temp = []
    funcao_a_bordo_temp = []
    for i, row in funcoes_dos_tripulantes.iterrows():
        trigrama = row['trigrama']
        funcoes_separadas = row['funcoes_a_bordo'].strip().split('/')
        for funcao in funcoes_separadas:
            trigramas_temp.append(trigrama)
            funcao_a_bordo_temp.append(funcao.strip())

    funcoes_tripulantes_df = pd.DataFrame({'trigrama': trigramas_temp,
                                           'funcao_a_bordo': funcao_a_bordo_temp})
    return funcoes_tripulantes_df
