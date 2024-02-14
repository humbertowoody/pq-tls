# Ansible

En este directorio se encuentra el proyecto de Ansible empleado para la configuración
de las instancias de AWS creadas por Terraform. El objetivo es instalar Python 3.12.1,
clonar el repositorio de código, crear un ambiente virtual, instalar las dependencias,
ejecutar las pruebas y, finalmente, descargar el archivo de resultados a la computadora
local.

## Pre-requisitos

Necesitas tener Python instalado en tu máquina local para poder usar Ansible.
También debes tener acceso a las instancias de AWS EC2 a través de SSH.

### Instalar Ansible

#### macOS:

Instala Ansible usando Homebrew con el siguiente comando:

```bash
brew install ansible
```

#### Linux (Ubuntu/Debian):

Agrega el PPA de Ansible y luego instala con `apt-get`:

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
```

### Configuración del inventario

Crea un archivo `hosts.ini` con la siguiente estructura, reemplazando `<ARM_INSTANCE_PUBLIC_IP>`
y `<X86_INSTANCE_PUBLIC_IP>` con las IPs públicas (o el DNS público provisto por
AWS) de tus instancias EC2:

```ini
[ubuntu_vms]
arm_instance ansible_host=<ARM_INSTANCE_PUBLIC_IP> ansible_user=ubuntu
x86_instance ansible_host=<X86_INSTANCE_PUBLIC_IP> ansible_user=ubuntu
```

### Ejecutar el playbook

Para ejecutar el playbook `setup.yml`, utiliza el siguiente comando:

```bash
ansible-playbook -i hosts.ini setup.yml
```

Esto instalará todas las dependencias, configurará el entorno Python y ejecutará
el script de pruebas en ambas instancias EC2. Los resultados serán descargados a
tu carpeta `~/Downloads`.

_Nota_: es importante que el usuario ubuntu tenga permiso de `sudoer`.
