# Terraform

Se utilizó Terraform para la definición del ambiente de pruebas a nivel
infraestructura, en la que se optó por dos instancias de EC2 ejecutando
Linux, Ubuntu 22.04, en dos arquitecturas distintas x86 y ARM, por lo que,
para el proveedor de nube AWS, las instancias elegidas fueron:

1. `t2.xlarge`: 4vCPU, 16GB RAM, x86 (amd64).
2. `t4g.xlarge`: 4vCPU, 16GB RAM, ARM (aarch64).

Se usó la región `us-east-1`.

## Instalar Terraform

Terraform es una herramienta de "Infrastructure as Code" que permite definir y
provisionar infraestructura en la nube de manera declarativa. Sigue las siguientes
instrucciones para instalar Terraform en tu sistema operativo.

### macOS:

Instala Terraform usando Homebrew con el siguiente comando:

```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

Para verificar la instalación, ejecuta:

```bash
terraform -version
```

### Linux (Ubuntu/Debian):

#### Instalar con apt-get (Ubuntu/Debian):

Agrega el repositorio oficial de HashiCorp y luego instala Terraform con `apt-get`:

```bash
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform
```

Para verificar la instalación, ejecuta:

```bash
terraform -version
```

Asegúrate de tener `curl` y `gnupg` instalados para agregar el repositorio de HashiCorp.

## Ejecución

Para ejecutar el script será necesario inicializar Terraform:

```
terraform init
```

Luego es prudente observar un plan de las tareas que Terraform realizará:

```
terraform plan
```

Se aplicará la configuración:

``` 
terraform apply
```

Una vez creada la infraestructura, se usó Ansible para ejecutar la configuración
de cada una de las instancias, ejecutar las pruebas y descargar los resultados.

Finalmente, destruimos la infraestructura:

```
terraform destroy
```
