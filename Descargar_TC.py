import pandas as pd
import requests
from datetime import datetime
import os

def descargar_y_formatear_tc():
    # 1. Parámetros de tiempo
    hoy = datetime.now()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    print(f"--- Iniciando Descarga y Formateo de Datos ---")
    
    # URL de la API de SUNAT
    url = f"https://api.apis.net.pe/v1/tipo-cambio-sunat?month={mes_actual}&year={anio_actual}"
    
    try:
        # 2. Descarga de datos (Extract)
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        
        # 3. Transformación de Texto (Format mm,dd,yyyy)
        # Convertimos el texto de la API a formato fecha y luego al texto exacto que pides
        df['fecha'] = pd.to_datetime(df['fecha']).dt.strftime('%m,%d,%Y')
        
        # 4. Organización de Columnas (Reorder)
        # Columna A: Fecha | Columna B: Venta | Columna C: Compra
        df_final = df[['fecha', 'venta', 'compra']].copy()
        df_final.columns = ['Fecha', 'Venta', 'Compra']
        
        # 5. Exportación (Load)
        ruta_directorio = r"C:\Users\aryhe\OneDrive\Documentos\Certus\DATA OPS"
        ruta_archivo = os.path.join(ruta_directorio, "TC_Mes_Actual.csv")
        
        # Guardamos sin índice para que no se cree una columna extra al inicio
        df_final.to_csv(ruta_archivo, index=False, encoding='utf-8')
        
        print(f"PROCESO EXITOSO")
        print(f"Archivo generado: {ruta_archivo}")
        print("Vista de Columnas (A, B, C):")
        print(df_final.head())

    except Exception as e:
        print(f"Error en el proceso de datos: {e}")

if __name__ == "__main__":
    descargar_y_formatear_tc()