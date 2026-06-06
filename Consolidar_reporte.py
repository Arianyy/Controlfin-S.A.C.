import pandas as pd
import glob
import os
import csv

# 1. Configuración de rutas
carpeta_reportes = r"C:\Users\aryhe\OneDrive\Documentos\Certus\DATA OPS\Reportes"
patron_archivos = os.path.join(carpeta_reportes, "Report Builder_*.csv")
archivos_encontrados = glob.glob(patron_archivos)

lista_movimientos_total = []
datos_resumen = [] 

print("--- Iniciando Consolidacion Completa (Sin omisiones) ---")

for ruta_archivo in archivos_encontrados:
    nombre_archivo = os.path.basename(ruta_archivo)
    
    try:
        origen = nombre_archivo.split("_")[1].split("(")[0].strip()
    except:
        origen = "Desconocido"

    filas_este_archivo = []
    suma_este_archivo = 0.0

    # Usamos el lector de CSV nativo para evitar errores de columnas
    with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
        lector = csv.DictReader(f)
        for fila in lector:
            monto_str = fila.get('Amount', '0').replace(',', '').replace('"', '').strip()
            
            try:
                monto_num = float(monto_str)
                if fila.get('Date'):
                    fila['Amount'] = monto_num 
                    fila['Origen_Cuenta'] = origen
                    filas_este_archivo.append(fila)
                    suma_este_archivo += monto_num
            except ValueError:
                continue 

    if filas_este_archivo:
        lista_movimientos_total.extend(filas_este_archivo)
        suma_individual = round(suma_este_archivo, 2)
        datos_resumen.append({'Cuenta': origen, 'Suma_Reporte_Original': suma_individual})
        print(f"Cuenta {origen}: procesada con suma de {suma_individual:,.2f}")

# 2. Procesamiento Final y Creación de Excel
if lista_movimientos_total:
    consolidado_final = pd.DataFrame(lista_movimientos_total)
    
    columnas = ['Origen_Cuenta'] + [col for col in consolidado_final.columns if col != 'Origen_Cuenta']
    consolidado_final = consolidado_final[columnas]

    total_final = round(consolidado_final['Amount'].sum(), 2)

    df_validacion = pd.DataFrame(datos_resumen)
    suma_de_partes = round(df_validacion['Suma_Reporte_Original'].sum(), 2)
    
    df_validacion['Total_Consolidado'] = total_final
    df_validacion['Diferencia'] = round(suma_de_partes - total_final, 2)
    df_validacion['Estado'] = df_validacion['Diferencia'].apply(lambda x: 'OK' if abs(x) < 0.01 else 'ERROR')

    archivo_salida = os.path.join(carpeta_reportes, "Reporte_Final_Con_Validacion.xlsx")
    
    with pd.ExcelWriter(archivo_salida) as writer:
        consolidado_final.to_excel(writer, sheet_name='Consolidado', index=False)
        df_validacion.to_excel(writer, sheet_name='Validacion', index=False)

    # IMPRESION FINAL CORREGIDA (Sin emojis y con variables correctas)
    print("\n" + "="*40)
    print("PROCESO COMPLETADO")
    print(f"Suma Total calculada: {total_final}")
    print(f"Ruta: {archivo_salida}")
    print("="*40)
else:
    print("No se encontraron datos validos en los archivos.")