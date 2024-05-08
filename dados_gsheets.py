from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time_handler
import streamlit as st


class Dados:
    url = r"https://docs.google.com/spreadsheets/d/1pHRfuc0vHjFLWdZ4DlX7OencLG6vIyCbtj53Jk88UR8/edit?usp=sharing"
    # Criando conexão com Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    ttl = 10 * 60

    def __init__(self):
        pass

    def generate_registros_voos_df(self):
        ID_registros_de_voos = "0"
        registros_de_voos_df = self.conn.read(spreadsheet=self.url, ttl=self.ttl, worksheet=ID_registros_de_voos)
        registros_de_voos_df['tempo_de_voo'] = registros_de_voos_df['tempo_de_voo'].astype(str)
        registros_de_voos_df['tempo_de_voo_minutos'] = registros_de_voos_df['tempo_de_voo'].map(
            time_handler.transform_duration_string_to_minutes)
        registros_de_voos_df['data_hora_dep'] = pd.to_datetime(registros_de_voos_df['data_hora_dep'],
                                                               format='%d/%m/%Y %H:%M:%S')
        registros_de_voos_df['data_hora_pouso'] = pd.to_datetime(registros_de_voos_df['data_hora_pouso'],
                                                                 format='%d/%m/%Y %H:%M:%S')

        return registros_de_voos_df

    def generate_detalhes_tripulantes_df(self):
        ID_detalhes_trip_voo = "1702473124"
        detalhes_tripulantes_df = self.conn.read(spreadsheet=self.url, ttl=self.ttl, worksheet=ID_detalhes_trip_voo)
        detalhes_tripulantes_df['data_voo'] = pd.to_datetime(detalhes_tripulantes_df['data_voo'],
                                                             format="%d/%m/%Y").dt.date
        detalhes_tripulantes_df['posicao_a_bordo'] = detalhes_tripulantes_df['posicao_a_bordo'].fillna(True)
        detalhes_tripulantes_df['posicao_a_bordo'] = detalhes_tripulantes_df['posicao_a_bordo'].map(
            lambda x: 'RSP' if x else 'LSP')

        registros_de_voos_df = self.generate_registros_voos_df()

        df1 = registros_de_voos_df[['IdVoo',
                                    'tempo_de_voo_minutos',
                                    'tempo_noturno',
                                    'tempo_ifr',
                                    'ifr_sem_pa',
                                    'arremetidas',
                                    'trafego_visual']]

        detalhes_tripulantes_df = detalhes_tripulantes_df.merge(df1, how='left')
        detalhes_tripulantes_df['data_voo'] = pd.to_datetime(detalhes_tripulantes_df['data_voo'])
        detalhes_tripulantes_df = detalhes_tripulantes_df[~detalhes_tripulantes_df['tripulante'].isin(['FIC',
                                                                                                       'HEL',
                                                                                                       'RND',
                                                                                                       'DGO',
                                                                                                       'BOS',
                                                                                                       'LET'])]
        return detalhes_tripulantes_df

    def generate_meta_pilotos_df(self):
        ID_meta_pilotos = "1746517579"
        meta_pilotos_df = self.conn.read(spreadsheet=self.url,
                                         ttl=self.ttl,
                                         worksheet=ID_meta_pilotos).drop(columns=['meta_comprep',
                                                                                  'meta_esquadrao'])
        meta_pilotos_df['meta_comprep_minutos'] = meta_pilotos_df['meta_comprep_minutos'] * 1000
        meta_pilotos_df['meta_esquadrao_minutos'] = meta_pilotos_df['meta_esquadrao_minutos'] * 1000
        meta_pilotos_df['meta_comprep'] = meta_pilotos_df['meta_comprep_minutos'].map(
            time_handler.transform_minutes_to_duration_string)
        meta_pilotos_df['meta_esquadrao'] = meta_pilotos_df['meta_esquadrao_minutos'].map(
            time_handler.transform_minutes_to_duration_string)

        return meta_pilotos_df

    def get_dados_pessoais(self):
        ID_dados_pessoais = "1235248626"
        dados_pessoais_df = self.conn.read(spreadsheet=self.url,
                                           worksheet=ID_dados_pessoais,
                                           ttl=self.ttl)

        dados_pessoais_df = dados_pessoais_df[~dados_pessoais_df['trigrama'].isin(['FIC',
                                                                                   'HEL',
                                                                                   'RND',
                                                                                   'DGO',
                                                                                   'BOS',
                                                                                   'LET'])]
        return dados_pessoais_df

    def get_OPO_df(self):
        ID_OPO = "117652390"
        OPO_df = self.conn.read(spreadsheet=self.url,
                                ttl=self.ttl,
                                worksheet=ID_OPO)
        return OPO_df

    def get_sobreaviso_df(self):
        ID_sobreaviso_df = "110642623"
        sobreaviso_df = self.conn.read(spreadsheet=self.url,
                                       ttl=self.ttl,
                                       worksheet=ID_sobreaviso_df)[['IdSobreaviso',
                                                                    'data',
                                                                    'localidade',
                                                                    'cor_portugues',
                                                                    'status_decod']]

        return sobreaviso_df

    def get_detalhes_tripulantes_sobreaviso(self):
        ID_detalhes_tripulantes_sobreaviso = "950795421"
        detalhes_tripulantes_sobreaviso_df = self.conn.read(spreadsheet=self.url,
                                                            ttl=self.ttl,
                                                            worksheet=ID_detalhes_tripulantes_sobreaviso)

        sobreaviso_df = self.get_sobreaviso_df()

        detalhes_tripulantes_sobreaviso_df = detalhes_tripulantes_sobreaviso_df.merge(sobreaviso_df,
                                                                                      how='left',
                                                                                      on='IdSobreaviso').drop(
            columns='IdTripulante')
        detalhes_tripulantes_sobreaviso_df = detalhes_tripulantes_sobreaviso_df.rename(
            columns={'tripulante': 'militar'})

        return detalhes_tripulantes_sobreaviso_df

    def get_sobreaviso_R99(self):
        ID_sobreaviso_R99 = "1866968545"
        sobreaviso_r99_df = self.conn.read(spreadsheet=self.url,
                                           ttl=self.ttl,
                                           worksheet=ID_sobreaviso_R99)[['IdSobreavisoR99',
                                                                         'data_inicial',
                                                                         'data_final',
                                                                         'localidade',
                                                                         'status_decod',
                                                                         ]]
        return sobreaviso_r99_df

    def get_detalhes_tripulantes_sobreaviso_R99(self):
        ID_detalhes_sobreaviso_R99 = "1776688925"
        detalhes_tripulantes_sobreaviso_r99_df = self.conn.read(spreadsheet=self.url,
                                                                ttl=self.ttl,
                                                                worksheet=ID_detalhes_sobreaviso_R99)
        sobreaviso_r99_df = self.get_sobreaviso_R99()
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
            range_dates = pd.date_range(start=row['data_inicial'], end=row['data_final'])
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
            detalhes_tripulantes_sobreaviso_r99_df_final['cor_portugues'].apply(self.generate_color)
        detalhes_tripulantes_sobreaviso_r99_df_final['data'] = detalhes_tripulantes_sobreaviso_r99_df_final[
            'data'].dt.strftime("%d/%m/%Y")

        return detalhes_tripulantes_sobreaviso_r99_df_final

    def generate_color(self, row):
        if row in [6, 5, 4]:
            return "Vermelho"
        else:
            return "Preto"

    def get_aeronaves(self):
        ID_aeronaves = "1102625224"
        aeronaves_df = self.conn.read(spreadsheet=self.url,
                                      ttl=self.ttl,
                                      worksheet=ID_aeronaves)
        return aeronaves_df

    def get_esforco_aereo(self):
        ID_esforco_aereo = "321112704"
        esforco_aereo_df = self.conn.read(spreadsheet=self.url,
                                          ttl=self.ttl,
                                          worksheet=ID_esforco_aereo)

        esforco_aereo_df['horas_alocadas_minutos'] = esforco_aereo_df['horas_alocadas'].map(
            time_handler.transform_duration_string_to_minutes)
        esforco_aereo_df['horas_gastas_minutos'] = esforco_aereo_df['horas_gastas'].map(
            time_handler.transform_duration_string_to_minutes)
        esforco_aereo_df['saldo_horas_minutos'] = esforco_aereo_df['saldo_horas'].map(
            time_handler.transform_duration_string_to_minutes)
        esforco_aereo_df = esforco_aereo_df.drop(columns=['IdEsfAer'])
        return esforco_aereo_df

    def get_planejamento_horas(self):
        ID_planejamento_horas = "1484335037"
        planejamento_horas_df = self.conn.read(spreadsheet=self.url,
                                               ttl=self.ttl,
                                               worksheet=ID_planejamento_horas)
        planejamento_horas_df['horas_planejadas_minutos'] = planejamento_horas_df['horas_planejadas'].map(
            time_handler.transform_duration_string_to_minutes)
        planejamento_horas_df['horas_voadas_minutos'] = planejamento_horas_df['horas_voadas'].map(
            time_handler.transform_duration_string_to_minutes)
        return planejamento_horas_df

    def get_aerodromos(self):
        ID_aerodromos = '614914780'
        aerodromos_df = self.conn.read(spreadsheet=self.url,
                                       ttl=self.ttl,
                                       worksheet=ID_aerodromos)
        return aerodromos_df

    def get_descidas(self):
        ID_descidas = "1926401618"
        descidas_df = self.conn.read(spreadsheet=self.url,
                                     ttl=self.ttl,
                                     worksheet=ID_descidas)
        return descidas_df
