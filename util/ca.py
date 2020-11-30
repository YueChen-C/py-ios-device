#!/usr/bin/env python
"""
@ Author：YueC
@ Description ：使用 cryptography 生成 rsa 加密算法
"""
import base64
import datetime

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import PublicFormat
from cryptography.x509 import NameOID
from pyasn1.codec.der import decoder as der_decoder
from pyasn1.codec.der import encoder as der_encoder
from pyasn1.type import univ


# rsa算法生成实例


def convertPKCS1toPKCS8pubKey(bitsdata):
    pubkey_pkcs1_b64 = b''.join(bitsdata.split(b'\n')[1:-2])
    pubkey_pkcs1, restOfInput = der_decoder.decode(base64.b64decode(pubkey_pkcs1_b64))
    bitstring = univ.Sequence()
    bitstring.setComponentByPosition(0, univ.Integer(pubkey_pkcs1[0]))
    bitstring.setComponentByPosition(1, univ.Integer(pubkey_pkcs1[1]))
    bitstring = der_encoder.encode(bitstring)
    try:
        bitstring = ''.join([('00000000' + bin(ord(x))[2:])[-8:] for x in list(bitstring)])
    except:
        bitstring = ''.join([('00000000' + bin(x)[2:])[-8:] for x in list(bitstring)])
    bitstring = univ.BitString("'%s'B" % bitstring)
    pubkeyid = univ.Sequence()
    pubkeyid.setComponentByPosition(0, univ.ObjectIdentifier('1.2.840.113549.1.1.1'))  # == OID for rsaEncryption
    pubkeyid.setComponentByPosition(1, univ.Null(''))
    pubkey_seq = univ.Sequence()
    pubkey_seq.setComponentByPosition(0, pubkeyid)
    pubkey_seq.setComponentByPosition(1, bitstring)
    base64.MAXBINSIZE = (64 // 4) * 3
    res = b"-----BEGIN PUBLIC KEY-----\n"
    res += base64.encodestring(der_encoder.encode(pubkey_seq))
    res += b"-----END PUBLIC KEY-----\n"
    return res


def generateRSAKey():
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    return key


def makePKey(key):
    public_key = key.public_key()
    return public_key


def makeRequest(public_key, cn):
    one_day = datetime.timedelta(1, 0, 0)
    builder = x509.CertificateBuilder() \
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn), ])) \
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"pyopenssl.org"), ])) \
        .not_valid_before(datetime.datetime.today() - one_day) \
        .not_valid_after(datetime.datetime.today() + one_day) \
        .serial_number(1) \
        .public_key(public_key) \
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)

    return builder


def makeCert(req, caPkey):
    pkey = req._public_key
    sub = req._subject_name
    one_day = datetime.timedelta(1, 0, 0)
    builder = x509.CertificateBuilder() \
        .subject_name(sub) \
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"pyopenssl.org"), ])) \
        .not_valid_before(datetime.datetime.today() - one_day) \
        .not_valid_after(datetime.datetime.today() + one_day) \
        .serial_number(1) \
        .public_key(pkey) \
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    certificate = builder.sign(
        private_key=caPkey, algorithm=hashes.SHA1(),
        backend=default_backend()
    )
    return certificate


def ca_do_everything(DevicePublicKey):
    _rsa = generateRSAKey()
    privateKey = makePKey(_rsa)
    req = makeRequest(privateKey, "The Issuer Monkey")
    cert = makeCert(req, _rsa)
    data = convertPKCS1toPKCS8pubKey(DevicePublicKey)
    rsa2 = serialization.load_pem_public_key(data, backend=default_backend())
    req = makeRequest(rsa2, "Device")
    cert2 = makeCert(req, _rsa)
    return cert.public_bytes(encoding=serialization.Encoding.PEM), \
           privateKey.public_bytes(encoding=serialization.Encoding.PEM,format=PublicFormat.SubjectPublicKeyInfo),\
           cert2.public_bytes(encoding=serialization.Encoding.PEM)


if __name__ == '__main__':
    _rsa = generateRSAKey()
    pkey = makePKey(_rsa)
    print(pkey.public_bytes(encoding=serialization.Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo))
    print(len(pkey.public_bytes(encoding=serialization.Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)))
    # req = makeRequest(pkey, 'YueChen')
    # cert = makeCert(req, _rsa)
    # data = b'-----BEGIN RSA PUBLIC KEY-----\nMIIBCgKCAQEAkF1xeOQEeN1mOqCDaEtIZ1TxGgrCt1OYMH+qibjPt1HS+uHBlkq6\r' \
    #        b'\nLMw7vyRjFdpmVbcieWH4hixXFAX2tS8sZaoAMYYDeRZRKdK4yAeNXegICkeVmbjO\r\nlqXJtavyv' \
    #        b'/RilbY0oO8vm6gOQ7Q18dRxRkNguKa8f5aJCv+SKQJ8XjHV2m3Qvx7y\r\nk+Ox6gTKuIUj1dSr/4NBbinduRFBnSxkD+PuJ5oqAt7j' \
    #        b'+QBb4uzWgxzBsvN3GIyt\r\n3/clTwBWdECGsw1z9X6SlFUjSCuqmejE4Aaf/fRfocds6z79rJN5XxuMnkyvARFo\r' \
    #        b'\nlPIGDgeh18eyzbUErPpAT9F9+8J/BJ54cwIDAQAB\n-----END RSA PUBLIC KEY-----\n '
    # a,b,c=ca_do_everything(data)
    # cert = makeCert(req, pkey)
    # print(cert.as_text())
    # cert.save_pem('my_ca_cert.pem')
