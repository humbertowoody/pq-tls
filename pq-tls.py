import socket
import time
import threading
from quantcrypt.kem import Kyber
from quantcrypt.dss import Dilithium
from Crypto.Cipher import AES
from Crypto.Hash import SHAKE256
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import sys

# Argumentos del programa
verificacion_dilithium = int(sys.argv[1])  # 0: Sin verificación, 1: Solo clientes, 2: Clientes y servidor
n_bytes = int(sys.argv[2])  # Cantidad N de bytes a transmitir

# Imprimimos los argumentos
print("Argumentos del programa:")
if verificacion_dilithium == 0:
    print("\t- No se realizará verificación de Dilithium.")
elif verificacion_dilithium == 1:
    print("\t- Se realizará verificación de Dilithium solo en los clientes.")
elif verificacion_dilithium == 2:
    print("\t- Se realizará verificación de Dilithium en los clientes y el servidor.")
else:
    print("\t- El primer argumento debe ser 0, 1 o 2.")
    exit()

print(f"\t- Se transmitirán {n_bytes} bytes.")


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

def servidor():
    kyber = Kyber()
    dilithium = Dilithium()
    clientes = {}

    # Generar par de claves de Dillithium.
    pk_dilithium, sk_dilithium = dilithium.keygen()

    # Generar el certificado con la clave privada de Dilithium.
    certificado = dilithium.sign(sk_dilithium, b'Certificado de servidor')

    # Abrimos un socket para escuchar conexiones
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print(f"Servidor: Escuchando en {HOST}:{PORT}")

        # Esperar a que se conecten dos clientes
        while len(clientes) < 2:
            conn, addr = s.accept()
            print(f"Servidor: Cliente {addr} conectado.")

            # Recibir Clave Pública del Cliente
            pk_cliente = conn.recv(1568)

            print(f"Servidor: Clave Pública KEM recibida del cliente {addr} con longitud {len(pk_cliente)} bytes.")

            # Encapsular y generar ciphertext
            ciphertext, shared_secret = kyber.encaps(pk_cliente)

            print(f"Servidor: Longitud del ciphertext generado para el cliente {addr}: {len(ciphertext)} bytes")
            print(f"Servidor: Longitud del shared_secret generado para el cliente {addr}: {len(shared_secret)} bytes")

            # Shakear para obtener la clave AES de 256 bits
            clave_aes = shake_key(shared_secret, 32)

            # Guardar la información del cliente
            clientes[addr] = (conn, pk_cliente, ciphertext, shared_secret, clave_aes)

            print(f"Servidor: Cliente {addr} registrado.")

        # Enviar el cyphertext a cada cliente.
        for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
            conn.send(ciphertext)
            print(f"Servidor: Ciphertext enviado al cliente {addr} con longitud {len(ciphertext)} bytes.")

        # Si se requiere verificación de Dilithium ya sea para el servidor o ambos, recibir el certificado y la
        # clave pública de Dilithium de ambos clientes y verificar la firma.
        if verificacion_dilithium == 1 or verificacion_dilithium == 2:
            print(f"Servidor: Recibiendo certificado y clave pública de Dilithium de los clientes.")
            # Recibir el certificado y la llave pública de dilithium del cliente y verificar.
            for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
                print(f"Servidor: Recibiendo certificado y clave pública de Dilithium del cliente {addr}.")
                certificado_cliente = conn.recv(4627)
                print(f"Servidor: Certificado recibido del cliente {addr} con longitud {len(certificado_cliente)} bytes.")
                pk_dilithium_cliente = conn.recv(2592)
                print(f"Servidor: Clave Pública Dilithium recibida del cliente {addr} con longitud {len(pk_dilithium_cliente)} bytes.")
                if dilithium.verify(pk_dilithium_cliente, b'Certificado de cliente', certificado_cliente):
                    print(f"Servidor: La firma del cliente {addr} es válida.")
                else:
                    print(f"Servidor: La firma del cliente {addr} NO es válida.")
                    return

        # Si la verificación del servidor está habilitada, enviar el certificado y la clave pública de Dilithium.
        if verificacion_dilithium == 2:
            print(f"Servidor: Enviando certificado y clave pública de Dilithium a los clientes.")
            for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
                conn.send(certificado)
                print(f"Servidor: Certificado enviado al cliente {addr} con longitud {len(certificado)} bytes.")
                conn.send(pk_dilithium)
                print(f"Servidor: Clave Pública Dilithium enviada al cliente {addr} con longitud {len(pk_dilithium)} bytes.")

        # Uno de los clientes enviará un mensaje en AES, lo descifraremos e imprimermos,
        # y posteriormente, cifraremos y enviaremos al otro cliente.
        cliente = 1
        mensaje = b''
        for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
            if cliente == 1:
                print(f"Servidor: Esperando mensaje cifrado del cliente {addr}.")
                mensaje_cifrado = conn.recv(1000001) #(n_bytes + AES.block_size)
                print(f"Servidor: Mensaje cifrado recibido del cliente {addr} con longitud {len(mensaje_cifrado)} bytes.")
                mensaje_descifrado = descifrar_aes(mensaje_cifrado, clave_aes)
                print(f"Servidor: Mensaje descifrado del cliente {addr}: {mensaje_descifrado}")
                mensaje = mensaje_descifrado
                cliente = 2
            else:
                print(f"Servidor: Enviando mensaje cifrado al cliente {addr}.")
                mensaje_cifrado = cifrar_aes(mensaje, clave_aes)
                conn.send(mensaje_cifrado)
                print(f"Servidor: Mensaje cifrado enviado al cliente {addr} con longitud {len(mensaje_cifrado)} bytes.")

        # Cerrar la Conexión
        for addr, (conn, pk_cliente, ciphertext, shared_secret, clave_aes) in clientes.items():
            conn.close()
            print(f"Servidor: Conexión con el cliente {addr} cerrada.")

        # Cerrar el socket
        s.close()
        print("Servidor: Socket cerrado.")



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

        print(f"Cliente {id_cliente}: Conectado al servidor.")

        # Enviar Clave Pública KEM al Servidor
        s.sendall(pk_kyber)


        print(f"Cliente {id_cliente}: Clave Pública KEM enviada al servidor con longitud {len(pk_kyber)} bytes.")

        # Recibir ciphertext del Servidor
        ciphertext = s.recv(1568)

        print(f"Cliente {id_cliente}: Ciphertext recibido del servidor con longitud {len(ciphertext)} bytes.")

        # Decapsular para obtener el shared_secret
        shared_secret = kyber.decaps(sk_kyber, ciphertext)

        print(f"Cliente {id_cliente}: Shared Secret decapsulado con longitud {len(shared_secret)} bytes.")

        # "Shakear" para obtener la clave AES de 256 bits
        clave_aes = shake_key(shared_secret, 32)

        print(f"Cliente {id_cliente}: Clave AES generada con longitud {len(clave_aes)} bytes.")

        # Si la verificación de cliente está habilitada, enviar el certificado y la clave pública de Dilithium.
        if verificacion_dilithium == 1 or verificacion_dilithium == 2:
            print(f"Cliente {id_cliente}: Enviando certificado y clave pública de Dilithium al servidor.")
            s.send(certificado)
            print(f"Cliente {id_cliente}: Certificado enviado al servidor con longitud {len(certificado)} bytes.")
            s.send(pk_dilithium)
            print(f"Cliente {id_cliente}: Clave Pública Dilithium enviada al servidor con longitud {len(pk_dilithium)} bytes.")

        # Si la verificación del servidor está habilitada, recibir el certificado y la calve pública de
        # Dilitium del servidor y verificar la firma.
        if verificacion_dilithium == 2:
            print(f"Cliente {id_cliente}: Recibiendo certificado y clave pública de Dilithium del servidor.")
            certificado_servidor = s.recv(4627)
            print(f"Cliente {id_cliente}: Certificado recibido del servidor con longitud {len(certificado_servidor)} bytes.")
            pk_dilithium_servidor = s.recv(2592)
            print(f"Cliente {id_cliente}: Clave Pública Dilithium recibida del servidor con longitud {len(pk_dilithium_servidor)} bytes.")

            if dilithium.verify(pk_dilithium_servidor, b'Certificado de servidor', certificado_servidor):
                print(f"Cliente {id_cliente}: La firma del servidor es válida.")
            else:
                print(f"Cliente {id_cliente}: La firma del servidor NO es válida.")
                return

        # Según el client_id, decidir si se envía o recibe el mensaje cifrado con AES.
        if id_cliente == 1:
            print(f"Cliente {id_cliente}: Generando mensaje aleatorio de {n_bytes} bytes y enviando al servidor.")
            mensaje_prueba = get_random_bytes(n_bytes)
            print(f"Cliente {id_cliente}: Mensaje aleatorio generado: {mensaje_prueba}")
            mensaje_cifrado = cifrar_aes(mensaje_prueba, clave_aes)
            print(f"Cliente {id_cliente}: Mensaje cifrado: {mensaje_cifrado}")
            s.send(mensaje_cifrado)
            print(f"Cliente {id_cliente}: Mensaje cifrado enviado al servidor con longitud {len(mensaje_cifrado)} bytes.")
        else:
            print(f"Cliente {id_cliente}: Esperando mensaje cifrado del servidor.")
            mensaje_cifrado = s.recv(1000001) #(n_bytes + AES.block_size)
            print(f"Cliente {id_cliente}: Mensaje cifrado recibido del servidor con longitud {len(mensaje_cifrado)} bytes.")
            if len(mensaje_cifrado) == 0:
                print(f"Cliente {id_cliente}: No se recibió mensaje del servidor.")
                return
            mensaje_descifrado = descifrar_aes(mensaje_cifrado, clave_aes)
            print(f"Cliente {id_cliente}: Mensaje descifrado del servidor: {mensaje_descifrado}")

        # Cerar la conexión
        s.close()

        print(f"Cliente {id_cliente}: Conexión cerrada.")

def iniciar_servidor():
    hilo_servidor = threading.Thread(target=servidor)
    hilo_servidor.start()

def iniciar_cliente(id_cliente):
    hilo_cliente = threading.Thread(target=cliente, args=(id_cliente,))
    hilo_cliente.start()
    return hilo_cliente

if __name__ == "__main__":
    iniciar_servidor()

    # Esperamos que el servidor esté listo
    time.sleep(1)

    # Iniciar los clientes
    hilo_cliente_1 = iniciar_cliente(1)
    time.sleep(1) # Pausa para simular que el cliente 1 se conecta antes que el cliente 2.
    hilo_cliente_2 = iniciar_cliente(2)

    # Esperar a que los clientes terminen
    hilo_cliente_1.join()
    hilo_cliente_2.join()

    print("Fin del programa.")

