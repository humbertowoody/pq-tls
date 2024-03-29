import socket
from platform import platform
import time
import threading
from quantcrypt.kem import Kyber
from quantcrypt.dss import Dilithium
from Crypto.Cipher import AES
from Crypto.Hash import SHAKE256
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import sys
import csv
import psutil
from os import getpid, path

# Función para imprimir
DEBUG = True
def imprimir(mensaje):
    if DEBUG:
        print(mensaje)

# Argumentos del programa
verificacion_dilithium = int(sys.argv[1])  # 0: Sin verificación, 1: Solo clientes, 2: Clientes y servidor
n_bytes = int(sys.argv[2])  # Cantidad N de bytes a transmitir

# Imprimimos los argumentos
imprimir("Argumentos del programa:")
if verificacion_dilithium == 0:
    imprimir("\t- No se realizará verificación de Dilithium.")
elif verificacion_dilithium == 1:
    imprimir("\t- Se realizará verificación de Dilithium solo en los clientes.")
elif verificacion_dilithium == 2:
    imprimir("\t- Se realizará verificación de Dilithium en los clientes y el servidor.")
else:
    imprimir("\t- El primer argumento debe ser 0, 1 o 2.")
    exit()

imprimir(f"\t- Se transmitirán {n_bytes} bytes.")

# Variables para mediciones
tiempo_inicio_kem  = 0
tiempo_fin_kem     = 0
cpu_inicio_kem     = 0
cpu_fin_kem        = 0
ram_inicio_kem     = 0
ram_fin_kem        = 0
tiempo_inicio_dss  = 0
tiempo_fin_dss     = 0
cpu_inicio_dss     = 0
cpu_fin_dss        = 0
ram_inicio_dss     = 0
ram_fin_dss        = 0
tiempo_inicio_aes  = 0
tiempo_fin_aes     = 0
cpu_inicio_aes     = 0
cpu_fin_aes        = 0
ram_inicio_aes     = 0
ram_fin_aes        = 0

servidor_listo = threading.Event()

# Parámetros de la conexión
HOST = '127.0.0.1'  # Dirección local para el servidor
PORT = 65432        # Puerto en el cual el servidor escuchará

def shake_key(clave, length=32):
    # Utilizar SHAKE256 para obtener una clave de 256 bits a partir del secreto compartido
    shake = SHAKE256.new()
    shake.update(clave)
    return shake.read(length)

def cifrar_aes(mensaje, clave):
    # Cifrar un mensaje utilizando AES en modo CBC
    cipher = AES.new(clave, AES.MODE_CBC)
    iv = cipher.iv
    ct_bytes = cipher.encrypt(pad(mensaje, AES.block_size))
    mensaje_cifrado = iv + ct_bytes
    return mensaje_cifrado

def descifrar_aes(ct, clave):
    # Descifrar un mensaje utilizando AES en modo CBC
    iv = ct[:AES.block_size]
    ct = ct[AES.block_size:]
    cipher = AES.new(clave, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt

def enviar(socket, datos):
    # Primero, enviamos la longitud de los datos como un entero de 64 bits
    longitud_datos = len(datos)
    socket.sendall(longitud_datos.to_bytes(8, byteorder='big'))

    # Luego, enviamos los datos en bloques
    inicio = 0
    while inicio < longitud_datos:
        fin = inicio + 4096  # Tamaño del bloque
        socket.sendall(datos[inicio:fin])
        inicio = fin

def recibir(socket):
    # Primero, recibimos la longitud de los datos
    datos_longitud = socket.recv(8)
    longitud_datos = int.from_bytes(datos_longitud, byteorder='big')

    # Luego, recibimos los datos en bloques
    datos = bytearray()
    bytes_recibidos = 0
    while bytes_recibidos < longitud_datos:
        bloque = socket.recv(min(4096, longitud_datos - bytes_recibidos))
        if not bloque:
            raise ConnectionError("Conexión cerrada antes de recibir todos los datos esperados")
        datos.extend(bloque)
        bytes_recibidos += len(bloque)

    return bytes(datos)

def servidor():
    global tiempo_inicio_kem, tiempo_fin_kem, cpu_inicio_kem, cpu_fin_kem, ram_inicio_kem, ram_fin_kem
    global tiempo_inicio_dss, tiempo_fin_dss, cpu_inicio_dss, cpu_fin_dss, ram_inicio_dss, ram_fin_dss
    global tiempo_inicio_aes, tiempo_fin_aes, cpu_inicio_aes, cpu_fin_aes, ram_inicio_aes, ram_fin_aes

    kyber = Kyber()
    dilithium = Dilithium()
    clientes = {}

    # Generar par de claves de Dillithium.
    pk_dilithium, sk_dilithium = dilithium.keygen()

    # Generar el certificado con la clave privada de Dilithium.
    certificado = dilithium.sign(sk_dilithium, b'Certificado de servidor')

    imprimir("Servidor: Iniciando servidor...")

    # Abrimos un socket para escuchar conexiones
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        imprimir("Servidor: Socket creado, iniciando servidor...")
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permitir reutilizar la dirección
        imprimir("Servidor: Socket configurado para reutilizar la dirección.")
        s.bind((HOST, PORT))
        imprimir(f"Servidor: Socket enlazado a {HOST}:{PORT}")
        s.listen()
        imprimir("Servidor: Escuchando conexiones")

        servidor_listo.set()

        imprimir(f"Servidor: Escuchando en {HOST}:{PORT}")

        # Medición: Inicio KEM.
        tiempo_inicio_kem = time.perf_counter()
        cpu_inicio_kem = time.process_time()
        ram_inicio_kem = psutil.Process(getpid()).memory_info().rss / (1024 ** 2)

        # Esperar a que se conecten dos clientes
        while len(clientes) < 2:
            conn, addr = s.accept()
            imprimir(f"Servidor: Cliente {addr} conectado.")

            # Recibir Clave Pública del Cliente
            pk_cliente = recibir(conn)

            imprimir(f"Servidor: Clave Pública KEM recibida del cliente {addr} con longitud {len(pk_cliente)} bytes.")

            # Encapsular y generar ciphertext
            ciphertext, shared_secret = kyber.encaps(pk_cliente)

            imprimir(f"Servidor: Longitud del ciphertext generado para el cliente {addr}: {len(ciphertext)} bytes")
            imprimir(f"Servidor: Longitud del shared_secret generado para el cliente {addr}: {len(shared_secret)} bytes")

            # Shakear para obtener la clave AES de 256 bits
            clave_aes = shake_key(shared_secret, 32)

            # Guardar la información del cliente
            clientes[addr] = (conn, pk_cliente, ciphertext, shared_secret, clave_aes)

            imprimir(f"Servidor: Cliente {addr} registrado.")

        # Enviar el cyphertext a cada cliente.
        for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
            enviar(conn, ciphertext)
            imprimir(f"Servidor: Ciphertext enviado al cliente {addr} con longitud {len(ciphertext)} bytes.")

        # Medición: Fin KEM.
        tiempo_fin_kem = time.perf_counter()
        cpu_fin_kem = time.process_time()
        ram_fin_kem = psutil.Process(getpid()).memory_info().rss / (1024 ** 2)

        # Medición: Inicio DSS.
        tiempo_inicio_dss = time.perf_counter()
        cpu_inicio_dss = time.process_time()
        ram_inicio_dss = psutil.Process(getpid()).memory_info().rss / (1024 ** 2)

        # Si se requiere verificación de Dilithium ya sea para el servidor o ambos, recibir el certificado y la
        # clave pública de Dilithium de ambos clientes y verificar la firma.
        if verificacion_dilithium == 1 or verificacion_dilithium == 2:
            imprimir(f"Servidor: Recibiendo certificado y clave pública de Dilithium de los clientes.")
            # Recibir el certificado y la llave pública de dilithium del cliente y verificar.
            for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
                imprimir(f"Servidor: Recibiendo certificado y clave pública de Dilithium del cliente {addr}.")
                certificado_cliente = recibir(conn)
                imprimir(f"Servidor: Certificado recibido del cliente {addr} con longitud {len(certificado_cliente)} bytes.")
                pk_dilithium_cliente = recibir(conn)
                imprimir(f"Servidor: Clave Pública Dilithium recibida del cliente {addr} con longitud {len(pk_dilithium_cliente)} bytes.")
                if dilithium.verify(pk_dilithium_cliente, b'Certificado de cliente', certificado_cliente):
                    imprimir(f"Servidor: La firma del cliente {addr} es válida.")
                else:
                    imprimir(f"Servidor: La firma del cliente {addr} NO es válida.")
                    return

        # Si la verificación del servidor está habilitada, enviar el certificado y la clave pública de Dilithium.
        if verificacion_dilithium == 2:
            imprimir(f"Servidor: Enviando certificado y clave pública de Dilithium a los clientes.")
            for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
                enviar(conn, certificado)
                imprimir(f"Servidor: Certificado enviado al cliente {addr} con longitud {len(certificado)} bytes.")
                enviar(conn, pk_dilithium)
                imprimir(f"Servidor: Clave Pública Dilithium enviada al cliente {addr} con longitud {len(pk_dilithium)} bytes.")

        # Medición: Fin DSS.
        tiempo_fin_dss = time.perf_counter()
        cpu_fin_dss = time.process_time()
        ram_fin_dss = psutil.Process(getpid()).memory_info().rss / (1024 ** 2)

        # Medición: Inicio AES.
        tiempo_inicio_aes = time.perf_counter()
        cpu_inicio_aes = time.process_time()
        ram_inicio_aes = psutil.Process(getpid()).memory_info().rss / (1024 ** 2)

        # Uno de los clientes enviará un mensaje en AES, lo descifraremos e imprimermos,
        # y posteriormente, cifraremos y enviaremos al otro cliente.
        cliente = 1
        mensaje = b''
        for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
            if cliente == 1:
                imprimir(f"Servidor: Esperando mensaje cifrado del cliente {addr}.")
                mensaje_cifrado = recibir(conn)
                imprimir(f"Servidor: Mensaje cifrado recibido del cliente {addr} con longitud {len(mensaje_cifrado)} bytes.")
                mensaje_descifrado = descifrar_aes(mensaje_cifrado, clave_aes)
                imprimir(f"Servidor: Mensaje descifrado del cliente {addr}: {mensaje_descifrado}")
                mensaje = mensaje_descifrado
                cliente = 2
            else:
                imprimir(f"Servidor: Enviando mensaje cifrado al cliente {addr}.")
                mensaje_cifrado = cifrar_aes(mensaje, clave_aes)
                enviar(conn, mensaje_cifrado)
                imprimir(f"Servidor: Mensaje cifrado enviado al cliente {addr} con longitud {len(mensaje_cifrado)} bytes.")

        # Medición: Fin AES.
        tiempo_fin_aes = time.perf_counter()
        cpu_fin_aes = time.process_time()
        ram_fin_aes = psutil.Process(getpid()).memory_info().rss / (1024 ** 2)

        # Cerrar la Conexión
        for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
            conn.close()
            imprimir(f"Servidor: Conexión con el cliente {addr} cerrada.")

        # Cerrar el socket
        s.close()
        imprimir("Servidor: Socket cerrado.")



def cliente(id_cliente):
    kyber = Kyber()
    dilithium = Dilithium()

    # Generar par de claves KEM
    pk_kyber, sk_kyber = kyber.keygen()

    # Generar par de claves de DSS.
    pk_dilithium, sk_dilithium = dilithium.keygen()

    # Firmar certificado con la clave privada de Dilithium.
    certificado = dilithium.sign(sk_dilithium, b'Certificado de cliente')

    # Conectarse al servidor
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        imprimir(f"Cliente {id_cliente}: Conectado al servidor.")

        # Enviar Clave Pública KEM al Servidor
        enviar(s, pk_kyber)


        imprimir(f"Cliente {id_cliente}: Clave Pública KEM enviada al servidor con longitud {len(pk_kyber)} bytes.")

        # Recibir ciphertext del Servidor
        ciphertext = recibir(s)

        imprimir(f"Cliente {id_cliente}: Ciphertext recibido del servidor con longitud {len(ciphertext)} bytes.")

        # Decapsular para obtener el shared_secret
        shared_secret = kyber.decaps(sk_kyber, ciphertext)

        imprimir(f"Cliente {id_cliente}: Shared Secret decapsulado con longitud {len(shared_secret)} bytes.")

        # "Shakear" para obtener la clave AES de 256 bits
        clave_aes = shake_key(shared_secret, 32)

        imprimir(f"Cliente {id_cliente}: Clave AES generada con longitud {len(clave_aes)} bytes.")

        # Si la verificación de cliente está habilitada, enviar el certificado y la clave pública de Dilithium.
        if verificacion_dilithium == 1 or verificacion_dilithium == 2:
            imprimir(f"Cliente {id_cliente}: Enviando certificado y clave pública de Dilithium al servidor.")
            enviar(s, certificado)
            imprimir(f"Cliente {id_cliente}: Certificado enviado al servidor con longitud {len(certificado)} bytes.")
            enviar(s, pk_dilithium)
            imprimir(f"Cliente {id_cliente}: Clave Pública Dilithium enviada al servidor con longitud {len(pk_dilithium)} bytes.")

        # Si la verificación del servidor está habilitada, recibir el certificado y la calve pública de
        # Dilitium del servidor y verificar la firma.
        if verificacion_dilithium == 2:
            imprimir(f"Cliente {id_cliente}: Recibiendo certificado y clave pública de Dilithium del servidor.")
            certificado_servidor = recibir(s)
            imprimir(f"Cliente {id_cliente}: Certificado recibido del servidor con longitud {len(certificado_servidor)} bytes.")
            pk_dilithium_servidor = recibir(s)
            imprimir(f"Cliente {id_cliente}: Clave Pública Dilithium recibida del servidor con longitud {len(pk_dilithium_servidor)} bytes.")

            if dilithium.verify(pk_dilithium_servidor, b'Certificado de servidor', certificado_servidor):
                imprimir(f"Cliente {id_cliente}: La firma del servidor es válida.")
            else:
                imprimir(f"Cliente {id_cliente}: La firma del servidor NO es válida.")
                return

        # Según el client_id, decidir si se envía o recibe el mensaje cifrado con AES.
        if id_cliente == 1:
            imprimir(f"Cliente {id_cliente}: Generando mensaje aleatorio de {n_bytes} bytes y enviando al servidor.")
            mensaje_prueba = get_random_bytes(n_bytes)
            imprimir(f"Cliente {id_cliente}: Mensaje aleatorio generado: {mensaje_prueba}")
            mensaje_cifrado = cifrar_aes(mensaje_prueba, clave_aes)
            imprimir(f"Cliente {id_cliente}: Mensaje cifrado: {mensaje_cifrado}")
            enviar(s, mensaje_cifrado)
            imprimir(f"Cliente {id_cliente}: Mensaje cifrado enviado al servidor con longitud {len(mensaje_cifrado)} bytes.")
        else:
            imprimir(f"Cliente {id_cliente}: Esperando mensaje cifrado del servidor.")
            mensaje_cifrado = recibir(s)
            imprimir(f"Cliente {id_cliente}: Mensaje cifrado recibido del servidor con longitud {len(mensaje_cifrado)} bytes.")
            if len(mensaje_cifrado) == 0:
                imprimir(f"Cliente {id_cliente}: No se recibió mensaje del servidor.")
                return
            mensaje_descifrado = descifrar_aes(mensaje_cifrado, clave_aes)
            imprimir(f"Cliente {id_cliente}: Mensaje descifrado del servidor: {mensaje_descifrado}")

        # Cerar la conexión
        s.close()

        imprimir(f"Cliente {id_cliente}: Conexión cerrada.")

def iniciar_servidor():
    hilo_servidor = threading.Thread(target=servidor)
    hilo_servidor.start()

    servidor_listo.wait()

def iniciar_cliente(id_cliente):
    hilo_cliente = threading.Thread(target=cliente, args=(id_cliente,))
    hilo_cliente.start()
    return hilo_cliente

if __name__ == "__main__":
    iniciar_servidor()

    # Iniciar los clientes
    hilo_cliente_1 = iniciar_cliente(1)
    hilo_cliente_2 = iniciar_cliente(2)

    # Esperar a que los clientes terminen
    hilo_cliente_1.join()
    hilo_cliente_2.join()

    # Calcular mediciones
    tiempo_total_kem = tiempo_fin_kem - tiempo_inicio_kem
    cpu_total_kem = cpu_fin_kem - cpu_inicio_kem
    ram_total_kem = ram_fin_kem
    tiempo_total_dss = tiempo_fin_dss - tiempo_inicio_dss
    cpu_total_dss = cpu_fin_dss - cpu_inicio_dss
    ram_total_dss = ram_fin_dss
    tiempo_total_aes = tiempo_fin_aes - tiempo_inicio_aes
    cpu_total_aes = cpu_fin_aes - cpu_inicio_aes
    ram_total_aes = ram_fin_aes

    # Extraemos la plataforma.
    plataforma = platform()

    # Imprimir mediciones
    imprimir("Mediciones:")
    imprimir(f"\t- Plataforma: {plataforma}")
    imprimir(f"\t- Tiempo total KEM: {tiempo_total_kem} segundos.")
    imprimir(f"\t- CPU total KEM: {cpu_total_kem} segundos.")
    imprimir(f"\t- RAM total KEM: {ram_total_kem} MB.")
    imprimir(f"\t- Tiempo total DSS: {tiempo_total_dss} segundos.")
    imprimir(f"\t- CPU total DSS: {cpu_total_dss} segundos.")
    imprimir(f"\t- RAM total DSS: {ram_total_dss} MB.")
    imprimir(f"\t- Tiempo total AES: {tiempo_total_aes} segundos.")
    imprimir(f"\t- CPU total AES: {cpu_total_aes} segundos.")
    imprimir(f"\t- RAM total AES: {ram_total_aes} MB.")

    # Escribir los resultados en un archivo CSV
    imprimir("Escribiendo resultados en el archivo CSV...")

    # Arreglo con los resultados
    resultados = [
        plataforma, verificacion_dilithium, n_bytes,
        tiempo_total_kem, tiempo_total_dss, tiempo_total_aes,
        cpu_total_kem, cpu_total_dss, cpu_total_aes,
        ram_total_kem, ram_total_dss, ram_total_aes
    ]

    # Formatear los números para mantener 8 decimales
    resultados_formateados = [f"{valor:.8f}" if isinstance(valor, float) else valor for valor in resultados]

    # Ruta al archivo CSV
    ruta_archivo = 'resultados.csv'

    # Verifica si el archivo existe para saber si debemos escribir los encabezados
    escribe_encabezados = not path.exists(ruta_archivo)

    with open(ruta_archivo, 'a', newline='', encoding='utf-8') as archivo:
        escritor_csv = csv.writer(archivo)

        # Si es la primera vez, escribe los encabezados
        if escribe_encabezados:
            escritor_csv.writerow([
                'plataforma', 'nivel_dss', 'cantidad_de_bytes_de_envio',
                'tiempo_kem', 'tiempo_dss', 'tiempo_mensaje',
                'cpu_kem', 'cpu_dss', 'cpu_mensaje',
                'ram_kem', 'ram_dss', 'ram_mensaje'
            ])

        # Escribe los resultados formateados
        escritor_csv.writerow(resultados_formateados)

    imprimir("Resultados añadidos al CSV con éxito.")

    imprimir("Fin del programa.")

