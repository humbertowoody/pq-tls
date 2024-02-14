# Ambiente de Pruebas
# Para la realización de las pruebas, se utilizaron, a modo de comparación, dos
# instancias de EC2, una con arquitectura ARM y otra con arquitectura x86.
# Ambas instancias se crearon en la región us-east-1 de AWS.
provider "aws" {
  region = "us-east-1"
}

# Instancia ARM
resource "aws_instance" "pq_tls_ubuntu_arm" {
  ami           = "ami-05d47d29a4c2d19e1"   # Ubuntu 22.04
  instance_type = "t4g.xlarge"              # 8 vCPUs, 16GB RAM, 64-bit ARM

  tags = {
    Name = "Ubuntu-ARM"
  }
}

# Instancia x86
resource "aws_instance" "pq_tls_ubuntu_x86" {
  ami           = "ami-0c7217cdde317cfec"   # Ubuntu 22.04
  instance_type = "t2.xlarge"               # 4 vCPUs, 16GB RAM, 64-bit x86

  tags = {
    Name = "Ubuntu-x86"
  }
}
