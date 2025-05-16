"""
create_dataframe.py

Este módulo contiene funciones para construir y consolidar DataFrames con los enlaces de productos extraídos y sus metadatos.
Incluye utilidades para asociar los links a su contexto (país, nombre, paginación, etc.) y para procesar múltiples URLs en paralelo.

Funciones:
- construir_dataframe_links: Construye un DataFrame con los links y metadatos asociados a una URL base.
- procesar_fila: Procesa una fila del DataFrame de URLs, extrayendo los links de productos.
- extraer_links_todas_las_urls: Extrae y consolida los links de productos de todas las URLs usando concurrencia.

Dependencias externas:
- Requiere funciones y patrones definidos en extraction.py y config.py.
- Utiliza pandas, concurrent.futures y tqdm para procesamiento y visualización de progreso.
"""

from packages import List, pd
from .extraction import extraer_links_url
from .config import posibles_subcadenas
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

#==========================
#--- Construir_dataframe_links
#==========================

def construir_dataframe_links(df_urls: pd.DataFrame, url_base: str, lista_links: List[str]) -> pd.DataFrame:
    """
    Construye un DataFrame con metadatos asociados a una URL base y una lista de links de productos.

    Args:
        df_urls (pd.DataFrame): DataFrame que contiene las URLs base y sus metadatos.
        url_base (str): URL base usada para extraer productos.
        lista_links (List[str]): Lista de URLs de productos extraídos.

    Returns:
        pd.DataFrame: DataFrame con cada link asociado a su contexto (país, nombre, paginación, etc).
    """
    # Validar que la URL base esté presente
    coincidencias = df_urls[df_urls['url final'] == url_base]
    
    if coincidencias.empty:
        print(f"[⚠️] construir_dataframe_links: No se encontró metadata para URL base: {url_base}")
        return pd.DataFrame()  # Devuelve DataFrame vacío si no hay coincidencias

    fila = coincidencias.iloc[0]

    # Crear el DataFrame final replicando los metadatos por cada link
    df_resultado = pd.DataFrame({
        'url final': lista_links,
        'Code Country': fila['Code Country'],
        'Country': fila['Country'],
        'Name': fila['Name'],
        'Information': fila['Information'],
        'Type Pagination': fila['Type Pagination'],
        'Note': fila['Note'],
        'Secuencia de paginacion': fila['Secuencia de paginacion']
    })

    print(f"construir_dataframe_links: Se creó el DataFrame con {len(lista_links)} links para {fila['Country']} - {fila['Name']}")
    return df_resultado

#==========================
#--- Procesar_fila
#==========================
def procesar_fila(df_urls: pd.DataFrame, fila: pd.Series) -> pd.DataFrame:
    url_base = fila['url final']
    try:
        sec_pag = int(fila['Secuencia de paginacion'])
    except ValueError:
        print(f"[⚠️] Error convirtiendo secuencia de paginación a int: {fila['Secuencia de paginacion']}")
        sec_pag = 1  # Valor por defecto

    links = extraer_links_url(
        url_base=url_base,
        sec_pag=sec_pag,
        posibles_subcadenas=posibles_subcadenas,
        pausa=5  # Puedes ajustar esto
    )

    if links:
        return construir_dataframe_links(df_urls, url_base, links)
    else:
        return pd.DataFrame()  # Devuelve vacío si no se extrajo nada
    
#==========================
#--- Extraer_links_todas_las_urls
#==========================
def extraer_links_todas_las_urls(df_urls: pd.DataFrame, max_workers: int = 50) -> pd.DataFrame:
    """
    Extrae links de productos de todas las URLs en el DataFrame.
    Utiliza múltiples hilos para acelerar el proceso.
    Args:
        df_urls (pd.DataFrame): DataFrame que contiene las URLs base y sus metadatos.
        max_workers (int): Número máximo de hilos a utilizar.
    Returns:
        pd.DataFrame: DataFrame consolidado con todos los links extraídos y sus metadatos.
    """
    resultados = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = [
            executor.submit(procesar_fila, df_urls, fila)
            for _, fila in df_urls.iterrows()
        ]

        for futuro in tqdm(as_completed(futuros), total=len(futuros), desc="Procesando URLs"):
            resultado = futuro.result()
            if not resultado.empty:
                resultados.append(resultado)

    if resultados:
        df_consolidado = pd.concat(resultados, ignore_index=True)
        print(f"[✅] Se extrajeron {len(df_consolidado)} links en total.")
        return df_consolidado
    else:
        print("[⚠️] No se extrajo ningún link.")
        return pd.DataFrame()
    

