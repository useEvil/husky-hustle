#!/bin/bash

openssl genrsa -out husky/certs/private_key.pem 1024
openssl req -new -key husky/certs/private_key.pem -x509 -days 365 -out husky/certs/public_key.pem
