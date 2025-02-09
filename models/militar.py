import time_handler
import datetime


class Militar:

    tempo_para_desadaptar_tripulantes = {
        'AL': 20,
        '1P': 35,
        'IN': 45, 
        'AC': 35,
        'MC': 45,
        'IC': 60,
        'AD-R': 35,
        'CO-R': 60,
        'ID-R': 75,
        'AB-R': 35,
        'CC-R': 60,
        'IB-R': 75,
        'AJ': 35,
        'CT': 60,
        'IJ': 75,
        'A3': 35,
        'O3': 60,
        'I3': 75,
        'A1': 35,
        'O1': 45,
        'I1': 60,
        'AA-E': 35,
        'MA-E': 45,
        'IA-E': 60,
        'AA-R': 35,
        'MA-R': 45,
        'IA-R': 60,
    }
    posicoes_a_bordo = ['LSP', 'RSP']
    funcoes_agrupadas = {'MEC': ['AC', 'MC', 'IC'],
                     'CC-R': ['AB-R', 'CC-R', 'IB-R'],
                     'COTAT': ['AJ', 'CT', 'IJ'],
                     'COAM-R': ['AD-R', 'CO-R', 'ID-R'],
                     'OE-3': ['A3', 'O3', 'I3'],
                     'OE-1': ['A1', 'O1', 'I1'],
                     'MA-R': ['AA-R', 'MA-R', 'IA-R'],
                     'MA-E': ['AA-E', 'MA-E', 'IA-E'],
                     'PIL': ['1P', '2P', 'AL', 'IN'],
                     'Pilotos (LSP/RSP)': posicoes_a_bordo}
    procedimentos = {
    'precisao': ['PAR', 'ILS'],
    'nao_precisao': ['LOC', 'VOR', 'NDB', 'RNAV/RNP']
}
    itens_cesta_basica = [
        'ifr_sem_pa',
        'arremetidas',
        'trafego_visual',
        'flape_22',
        'noturno',
        'precisao',
        'nao_precisao',
        *procedimentos['precisao'],
        *procedimentos['nao_precisao']]
    
    @classmethod
    def inicializar(cls):
        cls.funcoes_a_bordo = list(set([funcao_unica for funcao in cls.funcoes_agrupadas.values() for funcao_unica in funcao if funcao_unica not in cls.posicoes_a_bordo]))
    
    def __init__(self, voos=[], **kwargs):

        for key, value in kwargs.items():
            setattr(self, key, value)
    
        voos_realizados_pelo_militar = []
        for voo in voos:
            for tripulante in voo.tripulantes:
                if tripulante['tripulante'] == self.trigrama:
                    voos_realizados_pelo_militar.append(voo)
    
        self.voos_realizados = voos_realizados_pelo_militar
    
    @property
    def horas_militar(self):
        horas_de_voo = {
            'trigrama': self.trigrama,
            **{chave: 0 for chave in Militar.funcoes_a_bordo},
        }

        if 'PIL' in self.sigla_funcao:
            horas_de_voo['posicoes_a_bordo'] = {posicao: 0 for posicao in Militar.posicoes_a_bordo}
    


        for voo in self.voos_realizados:
            tempo_de_voo = voo.tempo_de_voo_minutos

            for tripulante in voo.tripulantes:
                if tripulante['tripulante'] == self.trigrama:
                    funcao_a_bordo = tripulante['funcao_a_bordo']
                    horas_de_voo[funcao_a_bordo] += tempo_de_voo

                    if 'PIL' in self.sigla_funcao and tripulante['posicao_a_bordo'] in Militar.posicoes_a_bordo:
                        posicao_a_bordo = tripulante['posicao_a_bordo']
                        horas_de_voo['posicoes_a_bordo'][posicao_a_bordo] += tempo_de_voo

        return horas_de_voo

    
    @property
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
    
    
    @property
    def adaptacao(self):
        funcoes_adaptacao = self.funcoes_a_bordo

        adaptacao = []
        for funcao_a_bordo in funcoes_adaptacao:
            ultimo_voo = self.checar_ultimo_voo(funcao_a_bordo)
            max_dias_sem_voar = Militar.tempo_para_desadaptar_tripulantes[funcao_a_bordo]
            voar_ate = ultimo_voo + datetime.timedelta(days=max_dias_sem_voar)
            dias_para_desadaptar = voar_ate - datetime.datetime.now()
            dias_sem_voar = datetime.datetime.now() - ultimo_voo
            label = "Adaptado" if voar_ate >= datetime.datetime.now() else "Desadaptado"
            
            adaptacao_funcao = {
                'trigrama': self.trigrama,
                'funcao_a_bordo': funcao_a_bordo,
                'ultimo_voo': ultimo_voo,
                'max_dias_sem_voar': max_dias_sem_voar,
                'voar_ate': voar_ate,
                'dias_para_desadaptar':dias_para_desadaptar,
                'dias_sem_voar': dias_sem_voar,
                'label': label
            }
            adaptacao.append(adaptacao_funcao)

        return adaptacao

    def checar_ultimo_voo(self, funcao):

        for chave, valor in Militar.funcoes_agrupadas.items():
            if funcao in valor:
                grupo_funcoes  = chave

        voos_realizados = self.voos_realizados

        voos_filtrados_para_funcao = [
            voo for voo in voos_realizados if any(tripulante['tripulante'] == self.trigrama and tripulante['funcao_a_bordo'] in Militar.funcoes_agrupadas[grupo_funcoes] for tripulante in voo.tripulantes)
            ]
        
        max_dias_sem_voar = Militar.tempo_para_desadaptar_tripulantes[funcao]
        default = datetime.datetime.now() - datetime.timedelta(days=max_dias_sem_voar + 1)
        ultimo_voo = max((voo.data_hora_pouso for voo in voos_filtrados_para_funcao), default=default)
        
        return ultimo_voo


    def servicos(self):
        pass


    def missoes_fora_de_sede(self):
        pass
    