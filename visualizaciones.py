# Visualizaciones
# Este script genera gráficas de barras para comparar los resultados promedio de las pruebas de rendimiento
# de los algoritmos KEM, DSS y Mensaje en función de la cantidad de bytes de envío, el nivel DSS y la plataforma.
# Las gráficas se guardan en la carpeta 'graficas' en formato PNG.
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Cargamos los resultados limpios a un Dataframe de Pandas.
df = pd.read_csv('resultados_promedio_limpios.csv')

# Creamos si no existe el directorio 'graficas'
os.makedirs('graficas', exist_ok=True)

# Eliminamos espacios en blanco al inicio y final de los nombres de las columnas
df.columns = df.columns.str.strip()

# Columnas a comparar
comparison_columns = ['tiempo_kem_promedio', 'tiempo_dss', 'tiempo_mensaje',
                      'cpu_kem', 'cpu_dss', 'cpu_mensaje',
                      'ram_kem', 'ram_dss', 'ram_mensaje']

# Convertir 'cantidad_de_bytes_de_envio' a categórico para una mejor representación en la gráfica de barras
df['cantidad_de_bytes_de_envio'] = pd.Categorical(df['cantidad_de_bytes_de_envio'])

# Convertir 'nivel_dss' a categórico para una mejor representación en la gráfica de barras
df['nivel_dss'] = pd.Categorical(df['nivel_dss'])

# Convertir 'plataforma' a categórico para una mejor representación en la gráfica de barras
df['plataforma'] = pd.Categorical(df['plataforma'])

# Gráfica de barras donde 'cantidad_de_bytes_de_envio' es la categoría principal
for column in comparison_columns:
    plt.figure(figsize=(10, 6))
    sns.barplot(x='cantidad_de_bytes_de_envio', y=column, hue='nivel_dss', data=df)
    plt.title(f'Comparación de {column} por Cantidad de Bytes y Nivel DSS')
    plt.xlabel('Cantidad de Bytes de Envío')
    plt.ylabel(column)
    plt.xticks(rotation=45)
    plt.legend(title='Nivel DSS')

    # Guardar la gráfica en la carpeta 'graficas'
    plt.savefig(f'graficas/{column}_por_cantidad_bytes.png')
    plt.clf()

# Gráfica de barras donde 'nivel_dss' es la categoría principal
for column in comparison_columns:
    plt.figure(figsize=(10, 6))
    sns.barplot(x='nivel_dss', y=column, hue='plataforma', data=df)
    plt.title(f'Comparación de {column} por Nivel DSS y Plataforma')
    plt.xlabel('Nivel DSS')
    plt.ylabel(column)
    plt.xticks(rotation=45)
    plt.legend(title='Plataforma')

    # Guardar la gráfica en la carpeta 'graficas'
    plt.savefig(f'graficas/{column}_por_nivel_dss.png')
    plt.clf()


# Gráfica de barras donde 'plataforma' es la categoría principal
for column in comparison_columns:
    plt.figure(figsize=(10, 6))
    sns.barplot(x='plataforma', y=column, hue='nivel_dss', data=df)
    plt.title(f'Comparación de {column} por Plataforma y Nivel DSS')
    plt.xlabel('Plataforma')
    plt.ylabel(column)
    plt.xticks(rotation=45)
    plt.legend(title='Nivel DSS')

    # Guardar la gráfica en la carpeta 'graficas'
    plt.savefig(f'graficas/{column}_por_plataforma.png')
    plt.clf()
