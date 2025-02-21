
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

procedimentos = {
'precisao': ['PAR', 'ILS'],
'nao_precisao': ['LOC', 'VOR', 'NDB', 'RNAV/RNP']}

funcoes_agrupadas_sem_valores = {'MEC': ['AC', 'MC', 'IC'],
'COTAT': ['AJ', 'CT', 'IJ'],
'CC-R': ['AB-R', 'CC-R', 'IB-R'],
'COAM-R': ['AD-R', 'CO-R', 'ID-R'],
'OE-3': ['A3', 'O3', 'I3'],
'OE-1': ['A1', 'O1', 'I1'],
'MA-R': ['AA-R', 'MA-R', 'IA-R'],
'MA-E': ['AA-E', 'MA-E', 'IA-E'],
'PIL': ['1P', '2P', 'AL', 'IN'],
'Pilotos (LSP/RSP)': posicoes_a_bordo}

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
