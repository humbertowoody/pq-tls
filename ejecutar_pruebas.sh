#!/bin/bash

# Definir las combinaciones de nivel de DSS
niveles_dss=(0 1 2)

# Definir las combinaciones de cantidad de bytes (1KB=1024 bytes, 10KB=10240 bytes, etc.)
cantidades_bytes=(1024 10240 102400 1048576)

# Número de iteraciones por combinación
NUM_ITERACIONES=150

# Ejecutar cada combinación NUM_ITERACIONES veces
for nivel in "${niveles_dss[@]}"; do
    for cantidad in "${cantidades_bytes[@]}"; do
        for (( i=1; i<=NUM_ITERACIONES; i++ )); do
            echo "Ejecutando prueba para nivel DSS $nivel con $cantidad bytes, iteración $i"
            python -u pq-tls.py $nivel $cantidad >> resultados.txt
        done
    done
done

