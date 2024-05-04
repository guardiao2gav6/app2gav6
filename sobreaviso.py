from databases import detalhes_tripulantes_sobreaviso, sobreaviso_df


df1 = sobreaviso_df[['IdSobreaviso',
                     'data',
                     'localidade',
                     'cor_portugues',
                     'status_decod']]

detalhes_tripulantes_sobreaviso = detalhes_tripulantes_sobreaviso.merge(df1, how='left', on='IdSobreaviso').drop(columns='IdTripulante')
detalhes_tripulantes_sobreaviso = detalhes_tripulantes_sobreaviso.rename(columns={'tripulante': 'militar'})
