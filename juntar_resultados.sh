#!/bin/bash

# Concatenar todos los archivos excepto el primero
cat resultados-x86.csv > resultados_completos.csv
for archivo in resultados-arm.csv resultados-m1.csv; do
    tail -n +2 $archivo >> resultados_completos.csv
done
