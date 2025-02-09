from streamlit_gsheets import GSheetsConnection
from urllib.error import URLError
import pandas as pd
import time_handler
import streamlit as st
from models.militar import Militar
from models.voo import Voo


class Dados:
    url = r"https://docs.google.com/spreadsheets/d/1pHRfuc0vHjFLWdZ4DlX7OencLG6vIyCbtj53Jk88UR8/edit?usp=sharing"
    conn = st.connection("gsheets", type=GSheetsConnection)
    ttl = 60 * 5

    def __init__(self):
        pass

    def connect_to_worksheet(self, id_worksheet):
        try:
            worksheet = self.conn.read(spreadsheet=self.url,
                                       ttl=self.ttl,
                                       worksheet=id_worksheet)
            return worksheet
        except URLError:
            return st.error("Verifique sua conexão com a internet")

    def generate_registros_voos_df(self, filtro_periodo, filtro_aeronave=['E-RR', 'R-99'], filtro_esforco_aereo=['SESQAE']):
        id_registros_de_voos = "0"
        registros_de_voos_df = self.connect_to_worksheet(
            id_worksheet=id_registros_de_voos)

        mascara = registros_de_voos_df['IdVoo'].notna() & (
            registros_de_voos_df['IdVoo'] != '')
        registros_de_voos_df = registros_de_voos_df[mascara]

        registros_de_voos_df['tempo_de_voo'] = registros_de_voos_df['tempo_de_voo'].astype(
            str)
        registros_de_voos_df['tempo_de_voo_minutos'] = registros_de_voos_df['tempo_de_voo'].map(
            time_handler.transform_duration_string_to_minutes)
        registros_de_voos_df['data_hora_dep'] = pd.to_datetime(registros_de_voos_df['data_hora_dep'],
                                                               format='%d/%m/%Y %H:%M:%S')
        registros_de_voos_df['data_hora_pouso'] = pd.to_datetime(registros_de_voos_df['data_hora_pouso'],
                                                                 format='%d/%m/%Y %H:%M:%S')

        registros_de_voos_df = registros_de_voos_df.loc[(
            registros_de_voos_df['data_hora_dep'].dt.date) >= filtro_periodo[0]]
        
        registros_de_voos_df = registros_de_voos_df.loc[registros_de_voos_df['aeronave'].isin(filtro_aeronave)]

        registros_de_voos_df = registros_de_voos_df.loc[registros_de_voos_df['esforco_aereo'].isin(filtro_esforco_aereo)]

        return registros_de_voos_df

    def get_voos(self, filtro_periodo, filtro_aeronave, filtro_esforco_aereo):
        registros_de_voos_df = self.generate_registros_voos_df(filtro_periodo, filtro_aeronave, filtro_esforco_aereo)

        id_detalhes_trip_voo = "1702473124"
        detalhes_tripulantes_df = self.connect_to_worksheet(
            id_worksheet=id_detalhes_trip_voo)
        detalhes_tripulantes_df['data_voo'] = pd.to_datetime(detalhes_tripulantes_df['data_voo'],
                                                             format="%d/%m/%Y").dt.date

        id_descidas = "1926401618"
        descidas = self.conn.read(spreadsheet=self.url,
                                  ttl=self.ttl,
                                  worksheet=id_descidas)

        voos = []
        for _, row in registros_de_voos_df.iterrows():
            voo = Voo(**row.to_dict())
            tripulantes_no_voo = detalhes_tripulantes_df[detalhes_tripulantes_df['IdVoo'] == voo.IdVoo].to_dict(
                orient="records")
            voo.tripulantes = tripulantes_no_voo

            descidas_no_voo = descidas[descidas['IdVoo']
                                       == voo.IdVoo].to_dict(orient='records')
            voo.descidas = descidas_no_voo

            voos.append(voo)

        return voos

    def generate_detalhes_tripulantes_df(self, filtro):
        id_detalhes_trip_voo = "1702473124"
        detalhes_tripulantes_df = self.connect_to_worksheet(
            id_worksheet=id_detalhes_trip_voo)
        detalhes_tripulantes_df['data_voo'] = pd.to_datetime(detalhes_tripulantes_df['data_voo'],
                                                             format="%d/%m/%Y").dt.date
        detalhes_tripulantes_df['posicao_a_bordo'] = detalhes_tripulantes_df['posicao_a_bordo'].fillna(
            True)

        registros_de_voos_df = self.generate_registros_voos_df(filtro_periodo=filtro)

        df1 = registros_de_voos_df[['IdVoo',
                                    'aeronave',
                                    'tempo_de_voo_minutos',
                                    'tempo_noturno',
                                    'tempo_ifr',
                                    'ifr_sem_pa',
                                    'arremetidas',
                                    'trafego_visual']]

        df1['tempo_noturno_minutos'] = df1['tempo_noturno'].map(
            time_handler.transform_duration_string_to_minutes)

        detalhes_tripulantes_df = detalhes_tripulantes_df.merge(
            df1, how='left')
        detalhes_tripulantes_df['data_voo'] = pd.to_datetime(
            detalhes_tripulantes_df['data_voo'])
        detalhes_tripulantes_df = detalhes_tripulantes_df[~detalhes_tripulantes_df['tripulante'].isin(['FIC',
                                                                                                       'HEL',
                                                                                                       'TAI',
                                                                                                       'RND',
                                                                                                       'TSU',
                                                                                                       'DGO',
                                                                                                       'BOS',
                                                                                                       'LET'])]
        
        st.write(detalhes_tripulantes_df)

        return detalhes_tripulantes_df

    def generate_meta_pilotos_df(self):
        id_meta_pilotos = "1746517579"
        meta_pilotos_df = self.connect_to_worksheet(id_worksheet=id_meta_pilotos).drop(columns=['meta_comprep',
                                                                                                'meta_esquadrao'])
        meta_pilotos_df = meta_pilotos_df.dropna()
        meta_pilotos_df['meta_comprep_minutos'] = meta_pilotos_df['meta_comprep_minutos'] * 1000
        meta_pilotos_df['meta_esquadrao_minutos'] = meta_pilotos_df['meta_esquadrao_minutos'] * 1000
        meta_pilotos_df['meta_comprep'] = meta_pilotos_df['meta_comprep_minutos'].map(
            time_handler.transform_minutes_to_duration_string)
        meta_pilotos_df['meta_esquadrao'] = meta_pilotos_df['meta_esquadrao_minutos'].map(
            time_handler.transform_minutes_to_duration_string)

        return meta_pilotos_df

    def get_dados_pessoais(self):
        id_dados_pessoais = "1235248626"
        dados_pessoais_df = self.connect_to_worksheet(
            id_worksheet=id_dados_pessoais)

        dados_pessoais_df = dados_pessoais_df[~dados_pessoais_df['trigrama'].isin(['FIC',
                                                                                   'HEL',
                                                                                   'TAI',
                                                                                   'TSU',
                                                                                   'RND',
                                                                                   'DGO',
                                                                                   'BOS',
                                                                                   'LET'])]
        return dados_pessoais_df

    def get_militares(self, filtro_periodo, filtro_aeronave, filtro_esforco_aereo):
        dados_pessoais_df = self.get_dados_pessoais()

        dados_pessoais_df['funcoes_a_bordo'] = dados_pessoais_df['funcoes_a_bordo'].apply(
            lambda x: x.split(" / "))
        dados_pessoais_df['sigla_funcao'] = dados_pessoais_df['sigla_funcao'].apply(
            lambda x: x.split("/"))
        
        voos = self.get_voos(filtro_periodo, filtro_aeronave, filtro_esforco_aereo)

        militares = []
        Militar.inicializar()
        for _, row in dados_pessoais_df.iterrows():
            
            militar = Militar(voos=voos, **row.to_dict())

            militares.append(militar)
        return militares

    def get_opo_df(self):
        id_opo = "117652390"
        opo_df = self.connect_to_worksheet(id_worksheet=id_opo)

        return opo_df

    def get_sobreaviso_df(self):
        id_sobreaviso_df = "110642623"
        sobreaviso_df = self.conn.read(spreadsheet=self.url,
                                       ttl=self.ttl,
                                       worksheet=id_sobreaviso_df)[['IdSobreaviso',
                                                                    'data',
                                                                    'localidade',
                                                                    'cor_portugues',
                                                                    'status_decod']]

        return sobreaviso_df

    def get_detalhes_tripulantes_sobreaviso(self):
        id_detalhes_tripulantes_sobreaviso = "950795421"
        detalhes_tripulantes_sobreaviso_df = self.conn.read(spreadsheet=self.url,
                                                            ttl=self.ttl,
                                                            worksheet=id_detalhes_tripulantes_sobreaviso)

        sobreaviso_df = self.get_sobreaviso_df()

        detalhes_tripulantes_sobreaviso_df = detalhes_tripulantes_sobreaviso_df.merge(sobreaviso_df,
                                                                                      how='left',
                                                                                      on='IdSobreaviso').drop(
            columns='IdTripulante')
        detalhes_tripulantes_sobreaviso_df = detalhes_tripulantes_sobreaviso_df.rename(
            columns={'tripulante': 'militar'})

        return detalhes_tripulantes_sobreaviso_df

    def get_sobreaviso_r99(self):
        id_sobreaviso_r99 = "1866968545"
        sobreaviso_r99_df = self.conn.read(spreadsheet=self.url,
                                           ttl=self.ttl,
                                           worksheet=id_sobreaviso_r99)[['IdSobreavisoR99',
                                                                         'data_inicial',
                                                                         'data_final',
                                                                         'localidade',
                                                                         'status_decod',
                                                                         ]]
        mascara_sa_r99 = sobreaviso_r99_df['IdSobreavisoR99'].notna() & (
            sobreaviso_r99_df['IdSobreavisoR99'] != '')
        sobreaviso_r99_df = sobreaviso_r99_df[mascara_sa_r99]

        return sobreaviso_r99_df

    def get_detalhes_tripulantes_sobreaviso_r99(self):
        id_detalhes_sobreaviso_r99 = "1776688925"
        detalhes_tripulantes_sobreaviso_r99_df = self.conn.read(spreadsheet=self.url,
                                                                ttl=self.ttl,
                                                                worksheet=id_detalhes_sobreaviso_r99)
        sobreaviso_r99_df = self.get_sobreaviso_r99()
        detalhes_tripulantes_sobreaviso_r99_df = detalhes_tripulantes_sobreaviso_r99_df.merge(
            sobreaviso_r99_df,
            how='left',
            on='IdSobreavisoR99').drop(
            columns='IdTripulante')
        detalhes_tripulantes_sobreaviso_r99_df = detalhes_tripulantes_sobreaviso_r99_df.rename(
            columns={'tripulante': 'militar'}
        )

        detalhes_tripulantes_sobreaviso_r99_df['data_inicial'] = pd.to_datetime(
            detalhes_tripulantes_sobreaviso_r99_df['data_inicial'],
            format="%d/%m/%Y")
        detalhes_tripulantes_sobreaviso_r99_df['data_final'] = pd.to_datetime(
            detalhes_tripulantes_sobreaviso_r99_df['data_final'],
            format="%d/%m/%Y")

        datas_list = []
        militares_list = []
        status_list = []
        for i, row in detalhes_tripulantes_sobreaviso_r99_df.iterrows():
            range_dates = pd.date_range(
                start=row['data_inicial'], end=row['data_final'])
            militar = row['militar']
            status = row['status_decod']
            for date in range_dates:
                datas_list.append(date)
                militares_list.append(militar)
                status_list.append(status)

        detalhes_tripulantes_sobreaviso_r99_df_final = pd.DataFrame({'data': datas_list,
                                                                     'militar': militares_list,
                                                                     'status_decod': status_list})
        detalhes_tripulantes_sobreaviso_r99_df_final['cor_portugues'] = \
            detalhes_tripulantes_sobreaviso_r99_df_final['data'].dt.weekday
        detalhes_tripulantes_sobreaviso_r99_df_final['cor_portugues'] = \
            detalhes_tripulantes_sobreaviso_r99_df_final['cor_portugues'].apply(
                self.generate_color)
        detalhes_tripulantes_sobreaviso_r99_df_final['data'] = detalhes_tripulantes_sobreaviso_r99_df_final[
            'data'].dt.strftime("%d/%m/%Y")

        return detalhes_tripulantes_sobreaviso_r99_df_final

    @staticmethod
    def generate_color(row):
        if row in [6, 5, 4]:
            return "Vermelho"
        else:
            return "Preto"

    def get_aeronaves(self):
        id_aeronaves = "1102625224"
        aeronaves_df = self.conn.read(spreadsheet=self.url,
                                      ttl=self.ttl,
                                      worksheet=id_aeronaves)
        return aeronaves_df

    def get_esforco_aereo(self):
        id_esforco_aereo = "321112704"
        esforco_aereo_df = self.conn.read(spreadsheet=self.url,
                                          ttl=self.ttl,
                                          worksheet=id_esforco_aereo)

        esforco_aereo_df['horas_alocadas_minutos'] = esforco_aereo_df['horas_alocadas'].map(
            time_handler.transform_duration_string_to_minutes)
        esforco_aereo_df['horas_gastas_minutos'] = esforco_aereo_df['horas_gastas'].map(
            time_handler.transform_duration_string_to_minutes)
        esforco_aereo_df['saldo_horas_minutos'] = esforco_aereo_df['saldo_horas'].map(
            time_handler.transform_duration_string_to_minutes)
        esforco_aereo_df = esforco_aereo_df.drop(columns=['IdEsfAer'])
        return esforco_aereo_df

    def get_planejamento_horas(self):
        id_planejamento_horas = "1484335037"
        planejamento_horas_df = self.conn.read(spreadsheet=self.url,
                                               ttl=self.ttl,
                                               worksheet=id_planejamento_horas)
        planejamento_horas_df['horas_planejadas_minutos'] = planejamento_horas_df['horas_planejadas'].map(
            time_handler.transform_duration_string_to_minutes)
        planejamento_horas_df['horas_voadas_minutos'] = planejamento_horas_df['horas_voadas'].map(
            time_handler.transform_duration_string_to_minutes)
        return planejamento_horas_df

    def get_aerodromos(self):
        id_aerodromos = '614914780'
        aerodromos_df = self.conn.read(spreadsheet=self.url,
                                       ttl=self.ttl,
                                       worksheet=id_aerodromos)
        return aerodromos_df

    def get_descidas(self):
        id_descidas = "1926401618"
        descidas_df = self.conn.read(spreadsheet=self.url,
                                     ttl=self.ttl,
                                     worksheet=id_descidas)
        return descidas_df


class DadosMissoesFora:
    url = r"https://docs.google.com/spreadsheets/d/1PzrB5qZBE3RLkgADivAQKDI5aclwHJYvKt5vaKeI1-c/edit?usp=sharing"
    conn = st.connection("gsheets", type=GSheetsConnection)
    ttl = 60 * 5

    def __init__(self):
        pass

    def connect_to_worksheet(self, id_worksheet):
        try:
            worksheet = self.conn.read(spreadsheet=self.url,
                                       ttl=self.ttl,
                                       worksheet=id_worksheet)
            return worksheet
        except URLError:
            return st.error("Verifique sua conexão com a internet")

    def get_comissionamentos(self):
        id_comiss = "1832401338"
        comiss_df = self.connect_to_worksheet(id_worksheet=id_comiss)
        comiss_df = comiss_df.loc[:, ~
                                  comiss_df.columns.str.contains('^Unnamed')]
        comiss_df = comiss_df.dropna(subset=['NUMERO DA OS'])
        comiss_df = comiss_df.rename(
            columns={"ATIVO (SIM) / INATIVO (NÃO) / PREVISTO (PREV)": 'Status'})

        return comiss_df
