import pandas as pd
import glob
import os
import csv

# 1. Configuración de rutas
# Cambiamos a la carpeta principal para encontrar el archivo de TC
carpeta_principal = r"C:\Users\aryhe\OneDrive\Documentos\Certus\DATA OPS"
carpeta_reportes = os.path.join(carpeta_principal, "Reportes")
ruta_tc = os.path.join(carpeta_principal, "TC_Mes_Actual.csv")

patron_archivos = os.path.join(carpeta_reportes, "Report Builder_*.csv")
archivos_encontrados = glob.glob(patron_archivos)

lista_movimientos_total = []
datos_resumen = [] 

print("--- Iniciando Consolidacion y Conversion (DataOps) ---")

# --- PASO A: LECTURA Y CONSOLIDACIÓN ---
for ruta_archivo in archivos_encontrados:
    nombre_archivo = os.path.basename(ruta_archivo)
    
    try:
        origen = nombre_archivo.split("_")[1].split("(")[0].strip()
    except:
        origen = "Desconocido"

    filas_este_archivo = []
    suma_este_archivo = 0.0

    with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
        lector = csv.DictReader(f)
        for fila in lector:
            monto_str = fila.get('Amount', '0').replace(',', '').replace('"', '').strip()
            
            try:
                monto_num = float(monto_str)
                # Verificamos que tenga fecha para evitar líneas de saldo final
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

# --- PASO B: CRUCE CON TIPO DE CAMBIO Y CÁLCULO ---
if lista_movimientos_total:
    # 1. Crear DataFrame base
    df_final = pd.DataFrame(lista_movimientos_total)
    
    # 2. Intentar cargar el Tipo de Cambio (descargado previamente)
    if os.path.exists(ruta_tc):
        df_tc = pd.read_csv(ruta_tc)
        
        # Unir por fecha (Date en Citibank, Fecha en nuestro CSV de SUNAT)
        df_final = pd.merge(
            df_final, 
            df_tc[['Fecha', 'Venta']], 
            left_on='Date', 
            right_on='Fecha', 
            how='left'
        )
        
        # Calcular columna en Soles
        df_final['Venta'] = df_final['Venta'].fillna(0) # Por si hay fechas sin TC
        df_final['Amount Soles'] = (df_final['Amount'] * df_final['Venta']).round(2)
        
        # Eliminar columna duplicada del cruce
        if 'Fecha' in df_final.columns:
            df_final = df_final.drop(columns=['Fecha'])
    else:
        print("ADVERTENCIA: No se encontro archivo de TC. Columnas de soles estaran en 0.")
        df_final['Venta'] = 0
        df_final['Amount Soles'] = 0

    # 3. Reordenar Columnas (Importante para la vista de ControlFin)
    cols_orden = ['Origen_Cuenta', 'Date', 'Amount', 'Venta', 'Amount Soles']
    otras_cols = [c for c in df_final.columns if c not in cols_orden]
    df_final = df_final[cols_orden + otras_cols]

    # 4. Validación de Totales
    total_usd = round(df_final['Amount'].sum(), 2)
    total_pen = round(df_final['Amount Soles'].sum(), 2)

    df_validacion = pd.DataFrame(datos_resumen)
    suma_de_partes = round(df_validacion['Suma_Reporte_Original'].sum(), 2)
    df_validacion['Total_Consolidado_USD'] = total_usd
    df_validacion['Diferencia'] = round(suma_de_partes - total_usd, 2)
    df_validacion['Estado'] = df_validacion['Diferencia'].apply(lambda x: 'OK' if abs(x) < 0.01 else 'ERROR')

    # --- PASO C: GUARDAR EXCEL FINAL ---
    archivo_salida = os.path.join(carpeta_principal, "Reporte_Final_Soles_Auditado.xlsx")
    
    with pd.ExcelWriter(archivo_salida) as writer:
        df_final.to_excel(writer, sheet_name='Consolidado_General', index=False)
        df_validacion.to_excel(writer, sheet_name='Validacion_USD', index=False)

    print("\n" + "="*40)
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print(f"Total General USD: {total_usd:,.2f}")
    print(f"Total General PEN: {total_pen:,.2f}")
    print(f"Archivo generado: {archivo_salida}")
    print("="*40)
else:
    print("No se encontraron datos validos para procesar.")