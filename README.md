# Post-Quantum TLS

This repository holds the implementation of a simple TLS with Post-Quantum
Cryptography implemented via Kyber for the KEM and Dilithium for the DSS.

## Requirements

To run this project, you'll need the following configurations on your local
environment:

- Python 3.12.1, recommended to be installed with `pyenv`.

## Installation

We assume you have `pyenv` on your local machine, so you would set your Python
version with:

``` 
pyenv local 3.12.1
```

After installation, you'll have to create the virtual environment with:

``` 
pyenv exec python -m venv ./venv
```

And activate said virtual environment:

```
source ./venv/bin/activate
```

Afterwards you'll install the dependencies with `pip`:

```
pip install -r requirements.txt
```

And that's it! :tada:

### Using Docker

In order to build the Docker image for this project, you can use the command:

```
docker buildx build --platform linux/amd64,linux/arm64 --push -t humbertowoody/pq-tls:latest .
```

In which we build for both x86 and ARM platforms (allowing us to run the same
code on a wide range of end-architectures) and subsequently push-and-tag the
resulting image onto a public registry for later consumption.

This guarantees you will be using the same environment used in the experiment.

## Running the project

The program itself takes two arguments:

```
python pq-tls.py <dss level> <bytes to transmit>
```

- `<dss level>`: refers to the DSS verification level which can take one of
  three values:
  1. `0`: no verification.
  2. `1`: Clients get verified by the Server.
  3. `2`: Clients get verified by the Server and the Server gets verified by the Clients.
- `<bytes to transmit>`: The amount of Bytes to transmit in the final AES messsage, refer
  to your specific OS configuration for the maximum buffer size as the program won't
  split and reconstruct large-amounts of data.

## Credits

- Gina Gallegos-García, Instituto Politécnico Nacional, CIC, Ciudad de México, México.
- Alfonso F. De Abiega-L’Eglisse, Tecnológico de Monterrey, CCM, Ciudad de México, México.
- Kevin A. Delgado Vargas, Instituto Politécnico Nacional, CIC, Ciudad de México, México.
- Michael Y. Serrano, Massachussetts Institute of Technology, Cambridge, United States of America.
- Humberto A. Ortega Alcocer, ESCOM, IPN, Ciudad de México, México.
