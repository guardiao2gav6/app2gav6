import streamlit as st
import requests
import missoes_fora_de_sede_service
from dados_gsheets import Dados, DadosMissoesFora


def get_cities_names():
    # URL da API do IBGE para obter todos os municípios
    url = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios'

    # Fazendo a requisição
    response = requests.get(url)
    municipios = response.json()

    # Extraindo apenas os nomes das cidades e estados
    cidades_ufs = [(municipio['nome'], municipio['microrregiao']['mesorregiao']['UF']['sigla']) for municipio in
                   municipios]

    # Imprimindo as cidades no formato Cidade - UF
    return cidades_ufs


dados = Dados()
dados_missoes_fora = DadosMissoesFora()
dados_pessoais_df = dados.get_dados_pessoais()
dados_comissionamentos = dados_missoes_fora.get_comissionamentos()
comiss_chart = missoes_fora_de_sede_service.gerar_grafico_dias_fora(dados_comissionamentos)

if st.checkbox(label='Mostrar Tabela'):
    st.dataframe(dados_comissionamentos)

trigramas = dados_pessoais_df['trigrama'].unique()
cidades = get_cities_names()
cidades = [" - ".join(cidade) for cidade in cidades]

st.altair_chart(comiss_chart, use_container_width=True)

with st.form('solicitacao_os'):
    st.markdown('##### Solicitar Ordem de Serviço')
    solicitante = st.selectbox(label='Solicitante', options=trigramas)
    email = st.text_input(label='Email')
    secao = st.selectbox(label='Seção do militar que solicita a OS', options=[
        'SSV',
        'SAP',
        'SOP',
        'SAM',
        '1ªESQDA',
        '2ªESQDA',
        '3ªESQDA',
    ])
    motivo_missao = st.text_input(label='Nome da missão')
    fispa = st.checkbox(label='Preciso de FISPA')
    local = st.selectbox(label='Local da missão (cidade e estado)', options=cidades)
    documento_autorizativo = st.text_input(label='Doc que autoriza a missão')
    data_ida = st.date_input(label='Data ida: ')
    data_volta = st.date_input(label='Data volta: ')
    militares = st.multiselect(label='Militares', options=trigramas)

    submitted = st.form_submit_button(label='Submit')
    if submitted:
        st.success('submetido com sucesso')
