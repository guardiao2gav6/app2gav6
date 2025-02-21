import time_handler
import datetime
import streamlit as st
from copy import deepcopy
from models import constantes


class Militar:

    def __init__(self, voos=[], filtro=None, **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)
                
        self.funcoes_agrupadas = {chave: {chave2: 0 for chave2 in valores} for chave, valores in constantes.funcoes_agrupadas_sem_valores.items()}

        self.voos_realizados = voos
        self.filtro = filtro
    
    def horas_militar(self):
        horas_de_voo = {
            'trigrama': self.trigrama,
            **{chave: valor for chave, valor in deepcopy(self.funcoes_agrupadas).items() if chave == self.filtro}
        }

        for voo in self.voos_realizados:
            tempo_de_voo = voo.tempo_de_voo_minutos

            for tripulante in voo.tripulantes:
                if tripulante['tripulante'] == self.trigrama:
                    funcao_a_bordo = tripulante['funcao_a_bordo']
                    posicao_a_bordo = tripulante['posicao_a_bordo']
                    if posicao_a_bordo in constantes.posicoes_a_bordo and self.filtro == 'Pilotos (LSP/RSP)':
                        grupo_funcao = 'Pilotos (LSP/RSP)'
                        horas_de_voo[self.filtro][posicao_a_bordo] += tempo_de_voo
                    else:
                        grupo_funcao = self.encontrar_grupo_da_funcao(funcao_a_bordo)
                    
                        if self.filtro and grupo_funcao == self.filtro:
                            horas_de_voo[self.filtro][funcao_a_bordo] += tempo_de_voo
                        elif self.filtro and grupo_funcao != self.filtro:
                            pass
                        else:
                            horas_de_voo[grupo_funcao][funcao_a_bordo] += tempo_de_voo
        horas_descompactado = {'trigrama': self.trigrama,
                               **deepcopy({chave: valor for chave, valor in deepcopy(horas_de_voo[self.filtro]).items()})}


        return deepcopy(horas_descompactado)

    
    def cesta_basica(self):
        cesta_basica = {
            'trigrama': self.trigrama,
            **{chave: 0 for chave in Militar.itens_cesta_basica},
        }

        for voo in self.voos_realizados:
            if any(x['tripulante'] == self.trigrama and x['funcao_a_bordo'] in ('1P', 'IN') for x in voo.tripulantes):
                
                voos_vars = vars(voo)
                for chave, valor in voos_vars.items():
                    if chave in cesta_basica and isinstance(cesta_basica[chave], (int, float)) and isinstance(valor, (int, float)):
                        cesta_basica[chave] += valor

                if time_handler.transform_duration_string_to_minutes(voo.tempo_noturno) > 0:
                    cesta_basica['noturno'] += 1
                
                for descida in voo.descidas:
                    cesta_basica[descida['procedimento']] += 1 * descida['quantidade']

        cesta_basica['precisao'] = sum(valor for chave, valor in cesta_basica.items() if chave in Militar.procedimentos['precisao'])
        cesta_basica['nao_precisao'] = sum(valor for chave, valor in cesta_basica.items() if chave in Militar.procedimentos['nao_precisao'])

        return cesta_basica
    
    
    def adaptacao(self, filtro_grupo):
        funcoes_adaptacao = self.funcoes_a_bordo
        grupo_funcoes = self.grupo_funcoes
        funcoes = grupo_funcoes[filtro_grupo]
        maior_funcao = list(set(funcoes) & set(funcoes_adaptacao))[0]
        hoje = datetime.datetime.now()
        ultimo_voo = self.checar_ultimo_voo(funcoes, maior_funcao)
        max_dias_sem_voar = constantes.tempo_para_desadaptar_tripulantes[maior_funcao]
        voar_ate = ultimo_voo + datetime.timedelta(days=max_dias_sem_voar)
        dias_para_desadaptar = voar_ate - hoje
        dias_sem_voar = hoje - ultimo_voo
        label = "Adaptado" if voar_ate >= hoje else "Desadaptado"
        
        if maior_funcao[0] == 'I':
            ordem = 1
        elif maior_funcao[0] == 'A':
            ordem = 3
        else:
            ordem = 2
        
        adaptacao_funcao = {
            'trigrama': self.trigrama,
            'funcao_a_bordo': maior_funcao,
            'ultimo_voo': ultimo_voo,
            'max_dias_sem_voar': max_dias_sem_voar,
            'data_limite_para_voar': voar_ate,
            'dias_para_desadaptar':dias_para_desadaptar.days,
            'dias_sem_voar': dias_sem_voar.days,
            'hoje': hoje,
            'label': label,
            'ordem': ordem
        }

        return adaptacao_funcao

    def checar_ultimo_voo(self, funcoes, maior_funcao):
        
        voos_realizados = self.voos_realizados

        voos_filtrados_para_funcao = [
            voo for voo in voos_realizados if any(tripulante['tripulante'] == self.trigrama and tripulante['funcao_a_bordo'] in funcoes for tripulante in voo.tripulantes)
            ]
        max_dias_sem_voar = constantes.tempo_para_desadaptar_tripulantes[maior_funcao]
        default = datetime.datetime.now() - datetime.timedelta(days=max_dias_sem_voar - 1)
        
        ultimo_voo = max((voo.data_hora_pouso for voo in voos_filtrados_para_funcao), default=default)
        
        return ultimo_voo


    def servicos(self):
        pass


    def missoes_fora_de_sede(self):
        pass
    
    def encontrar_grupo_da_funcao(self, funcao):
        return next((chave for chave, valores in self.funcoes_agrupadas.items() if funcao in valores), None)