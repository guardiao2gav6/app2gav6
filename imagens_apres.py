from pages.Pilotos import grafico_pau_de_sebo, grafico_adaptacao

grafico_pau_de_sebo.properties(width=1100,
                               height=300).configure_legend(labelFontSize=14,
                                                            titleFontSize=16).configure_axis(domain=False,
                                                                                             ticks=False).save(
    'chart.svg')

grafico_adaptacao.properties(width=1100,
                             height=300).configure_legend(labelFontSize=14,
                                                          titleFontSize=16).configure_axis(domain=False,
                                                                                           ticks=False).save(
    'chart_adaptacao.svg')
