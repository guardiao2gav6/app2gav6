import datetime
import re
import streamlit as st
from dados_gsheets import Dados
import math
import time_handler
import pandas as pd


class Ponto:
    def __init__(self,
                 nome: str = '',
                 isdep: bool = False,
                 ispouso: bool = False,
                 isonstation: bool = False,
                 horario_onstation=None):

        self.lat = None
        self.lon = None
        self.isdep = isdep
        self.ispouso = ispouso
        self.isonstation = isonstation
        self.horario_onstation = horario_onstation
        self.nome = nome


class Aerodromo(Ponto):
    def __init__(self, aerodromo, isdep=False, ispouso=False, isonstation=False, horario_onstation=None):

        super().__init__(
            nome=aerodromo,
            isdep=isdep,
            ispouso=ispouso,
            isonstation=isonstation,
            horario_onstation=horario_onstation)

        self.lat = float(
            aerodromos.loc[aerodromos['codigo_icao'] == aerodromo, 'latlong'].iloc[0].split(', ')[0].strip())
        self.lon = float(
            aerodromos.loc[aerodromos['codigo_icao'] == aerodromo, 'latlong'].iloc[0].split(', ')[1].strip())


class Coordenadas(Ponto):
    def __init__(self, latitude: str, longitude: str, isdep=False, ispouso=False, isonstation=False, horario_onstation=None):

        super().__init__(
            nome=f'{latitude} / {longitude}',
            isdep=isdep,
            ispouso=ispouso,
            isonstation=isonstation,
            horario_onstation=horario_onstation)

        regex_lat = r'^(\d{1,3})°\s*(\d{1,2})(?:\.(\d{1,2}))?\'\s*([NSns])$'
        regex_lon = r'^(\d{1,3})°\s*(\d{1,2})(?:\.(\d{1,2}))?\'\s*([EWew])$'

        # Tentar encontrar correspondência na coordenada fornecida
        match_lat = re.match(regex_lat, latitude)
        match_lon = re.match(regex_lon, longitude)

        if match_lat:
            # Extrair grupos capturados
            graus_lat = int(match_lat.group(1))
            minutos_lat = int(match_lat.group(2))
            segundos_lat = float(match_lat.group(3) or 0)  # Se não houver valor de segundos, assume 0
            direcao_lat = match_lat.group(4)

            # Converter para decimal
            decimal_lat = graus_lat + minutos_lat / 60 + segundos_lat / 3600

            # Verificar a direção e ajustar o sinal
            if direcao_lat in ['S', 's']:
                decimal_lat = -decimal_lat

            # Retornar o valor com 6 casas decimais
            self.lat = round(decimal_lat, 6)

        else:
            self.lat = None

        if match_lon:
            # Extrair grupos capturados
            graus_lon = int(match_lon.group(1))
            minutos_lon = int(match_lon.group(2))
            segundos_lon = float(match_lon.group(3) or 0)  # Se não houver valor de segundos, assume 0
            direcao_lon = match_lon.group(4)

            # Converter para decimal
            decimal_lon = graus_lon + minutos_lon / 60 + segundos_lon / 3600

            # Verificar a direção e ajustar o sinal
            if direcao_lon in ['W', 'w']:
                decimal_lon = -decimal_lon

            # Retornar o valor com 6 casas decimais
            self.lon = round(decimal_lon, 6)

        else:
            self.lon = None


class RadialDistancia(Ponto):
    def __init__(self):
        super().__init__()
        pass


class Trecho:
    def __init__(self, ponto_inicial: Ponto, ponto_final: Ponto):
        self.ponto_inicial = ponto_inicial
        self.ponto_final = ponto_final
        self.distancia = haversine(self.ponto_inicial, self.ponto_final)
        self.tempo = gerando_tempos(self.distancia)
        self.tempo_formatado = time_handler.transform_minutes_to_duration_string(self.tempo * 60)
        self.nome_trecho = f"{self.ponto_inicial.nome} - {self.ponto_final.nome}"
        self.pouso_datetime = None
        self.pouso_formatado = None
        self.pronto_datetime = None
        self.pronto_formatado = None
        self.dep_datetime = None
        self.dep_formatado = None
        self.on_station_datetime = None
        self.horario_onstation_formatado = None
        self.aprestamento_datetime = None
        self.aprestamento_formatado = None

        if ponto_final.isonstation:
            self.on_station_datetime = ponto_final.horario_onstation
            self.horario_onstation_formatado = self.on_station_datetime.time().strftime("%H:%M")
            self.dep_datetime = self.on_station_datetime - datetime.timedelta(hours=self.tempo)
            self.dep_formatado = self.dep_datetime.time().strftime("%H:%M")
            self.pronto_datetime = self.dep_datetime - datetime.timedelta(hours=0.5)
            self.pronto_formatado = self.pronto_datetime.time().strftime("%H:%M")
            self.aprestamento_datetime = self.pronto_datetime - datetime.timedelta(hours=1.5)
            self.aprestamento_formatado = self.aprestamento_datetime.time().strftime("%H:%M")

        else:
            pass


def haversine(ponto1, ponto2):

    lat1 = ponto1.lat
    lon1 = ponto1.lon

    lat2 = ponto2.lat
    lon2 = ponto2.lon

    # Converte graus decimais para radianos
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Diferença entre as latitudes e longitudes
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Fórmula de Haversine
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Raio da Terra em km
    radius_earth = 6371.0

    # Calcula a distância
    distance = round((radius_earth * c) / 1.852)

    return distance


def gerando_tempos(dist):
    if dist < 30:
        elemento = (dist / velocidade_corrigida) + (10 / 60)
    else:
        elemento = (dist / velocidade_corrigida)

    return elemento


# Carregando dados
dados = Dados()
aerodromos = dados.get_aerodromos()
codigos_icao = aerodromos['codigo_icao']

# TIPO, HORARIO E DATA DO PONTO ON STATION
opcoes_ponto_onstation = ['Vertical de Aeródromo',
                          "Coordenada Geográfica GMC",
                          'Radial/Distância de Aeródromo']

tipo_ponto_on_station = st.radio(label='Tipo de ponto ON STATION',
                                 options=opcoes_ponto_onstation)

if tipo_ponto_on_station == opcoes_ponto_onstation[0]:
    aerodromo_onstation = st.selectbox(label='Aeródromo', options=codigos_icao)
    ponto_onstation_selecionado = Aerodromo(aerodromo_onstation, isonstation=True)

elif tipo_ponto_on_station == opcoes_ponto_onstation[1]:
    latitude_onstation = st.text_input(label='Latitude (N/S)', value="05°05.05'N")
    longitude_onstation = st.text_input(label='Longitude (E/W)', value="060°05.50'W")
    ponto_onstation_selecionado = Coordenadas(latitude_onstation, longitude_onstation, isonstation=True)
    st.write(f'A coordenada corrigida é {ponto_onstation_selecionado.lat} / {ponto_onstation_selecionado.lon}')

elif tipo_ponto_on_station == opcoes_ponto_onstation[2]:
    radial_distancia_onstation = st.text_input(label='Radia/Dist.', placeholder='XXX/XXX')
    ponto_onstation_selecionado = RadialDistancia()
else:
    ponto_onstation_selecionado = None

data_onstation = st.date_input(label='Data ON STATION')
horario_onstation_input = st.time_input(label='Horário ON STATION (Z)')
datetime_onstation = datetime.datetime.combine(data_onstation, horario_onstation_input)
ponto_onstation_selecionado.horario_onstation = datetime_onstation

# AERÓDROMO DE DEP, POUSO E VELOCIDADE DA ANV
aerodromo_dep = st.selectbox(label='Aeródromo de Decolagem',
                             options=codigos_icao)
aerodromo_dep_selecionado = Aerodromo(aerodromo_dep, isdep=True)

aerodromo_recolhimento = st.selectbox(label='Aeródromo de recolhimento',
                                      options=codigos_icao)
aerodromo_recolhimento_selecionado = Aerodromo(aerodromo_recolhimento, ispouso=True)

velocidade_anv = st.number_input(label='Velocidade da aeronave em Kt', value=360, step=0)
velocidade_corrigida = 0.85 * velocidade_anv

# TIPOS DE DESLOCAMENTO
opcoes_tipo_deslocamento = ['Decolagem DCT ON STATION', 'Farei pousos intermediários']
tipo_deslocamento = st.radio(label='Tipo de deslocamento até ON STATION',
                             options=opcoes_tipo_deslocamento)

if tipo_deslocamento == opcoes_tipo_deslocamento[0]:
    rota_completa = [aerodromo_dep_selecionado, ponto_onstation_selecionado]
elif tipo_deslocamento == opcoes_tipo_deslocamento[1]:
    aerodromos_rota = st.multiselect(label='Selecione os aerodrómos da sua rota até o ON STATION',
                                     options=codigos_icao)
    rota_completa = [aerodromo_dep_selecionado] + \
                    [Aerodromo(aerodromo) for aerodromo in aerodromos_rota] + \
                    [ponto_onstation_selecionado]
else:
    rota_completa = []

st.markdown('---')


lista_par_de_pontos = list(zip(rota_completa, rota_completa[1:]))
lista_trechos = list(map(lambda x: Trecho(ponto_inicial=x[0],
                                          ponto_final=x[1]), lista_par_de_pontos))
lista_trechos = list(reversed(lista_trechos))


for i in range(len(lista_trechos)):
    trecho_atual = lista_trechos[i]
    if i > 0:
        trecho_anterior = lista_trechos[i - 1]
    else:
        trecho_anterior = None

    if not trecho_atual.ponto_final.isonstation:
        trecho_atual.pouso_datetime = trecho_anterior.aprestamento_datetime
        trecho_atual.pouso_formatado = trecho_anterior.aprestamento_formatado
        trecho_atual.dep_datetime = trecho_atual.pouso_datetime - datetime.timedelta(hours=trecho_atual.tempo)
        trecho_atual.dep_formatado = trecho_atual.dep_datetime.time().strftime("%H:%M")
        trecho_atual.pronto_datetime = trecho_atual.dep_datetime - datetime.timedelta(hours=0.5)
        trecho_atual.pronto_formatado = trecho_atual.pronto_datetime.time().strftime("%H:%M")
        trecho_atual.aprestamento_datetime = trecho_atual.pronto_datetime - datetime.timedelta(hours=1.5)
        trecho_atual.aprestamento_formatado = trecho_atual.aprestamento_datetime.time().strftime("%H:%M")


tabela_resultados = pd.DataFrame({
    'Trecho': [trecho.nome_trecho for trecho in lista_trechos],
    'Aprest': [trecho.aprestamento_formatado for trecho in lista_trechos],
    'Pronto': [trecho.pronto_formatado for trecho in lista_trechos],
    'DEP': [trecho.dep_formatado for trecho in lista_trechos],
    'TEV': [trecho.tempo_formatado for trecho in lista_trechos],
    'ON STATION': [trecho.horario_onstation_formatado for trecho in lista_trechos],
    'Pouso': [trecho.pouso_formatado for trecho in lista_trechos]

})
tabela_resultados = tabela_resultados.iloc[::-1]
tabela_resultados = tabela_resultados.reset_index(drop=True)

st.markdown("#### Resultado")

st.dataframe(tabela_resultados, use_container_width=True)
