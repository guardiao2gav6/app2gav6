def transform_minutes_to_duration_string(time_minutes):

    minutos_totais = abs(time_minutes)
    hora = int((minutos_totais / 60) // 1)
    minutos = int(minutos_totais - hora * 60)
    if time_minutes < 0:
        return f'-{str(hora).zfill(2)}:{str(minutos).zfill(2)}'
    else:
        return f'{str(hora).zfill(2)}:{str(minutos).zfill(2)}'


def transform_duration_string_to_minutes(duration_string):
    new_duration_string = duration_string.replace('-', '')
    try:
        horas, minutos, segundos = new_duration_string.split(':')
    except ValueError:
        horas, minutos = new_duration_string.split(':')
    total_minutos = (int(horas) * 60) + int(minutos)
    if duration_string[0] == '-':
        return -total_minutos
    else:
        return total_minutos
