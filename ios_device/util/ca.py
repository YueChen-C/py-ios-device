import base64

from datetime import datetime, timedelta

from OpenSSL.crypto import X509, TYPE_RSA, X509Req, PKey, FILETYPE_PEM as PEM, X509Name, X509Extension
from OpenSSL.crypto import load_publickey, dump_privatekey, dump_certificate
from pyasn1.type import univ
from pyasn1.codec.der import encoder as der_encoder, decoder as der_decoder
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

__all__ = ['make_certs_and_key']


def make_certs_and_key(device_public_key: bytes):
    priv_key = PKey()
    priv_key.generate_key(TYPE_RSA, 2048)

    req = make_req(priv_key)
    cert = make_cert(req, priv_key)

    dev_key = load_publickey(PEM, convert_PKCS1_to_PKCS8_pubkey(device_public_key))
    dev_key._only_public = False
    dev_req = make_req(dev_key, 'Device')
    dev_cert = make_cert(dev_req, priv_key)

    return dump_certificate(PEM, cert), dump_privatekey(PEM, priv_key), dump_certificate(PEM, dev_cert)


def convert_PKCS1_to_PKCS8_pubkey(data: bytes) -> bytes:
    pubkey_pkcs1_b64 = b''.join(data.split(b'\n')[1:-2])
    pubkey_pkcs1, restOfInput = der_decoder.decode(base64.b64decode(pubkey_pkcs1_b64))
    bit_str = univ.Sequence()
    bit_str.setComponentByPosition(0, univ.Integer(pubkey_pkcs1[0]))
    bit_str.setComponentByPosition(1, univ.Integer(pubkey_pkcs1[1]))
    bit_str = der_encoder.encode(bit_str)
    try:
        bit_str = ''.join([('00000000' + bin(ord(x))[2:])[-8:] for x in list(bit_str)])
    except Exception:
        bit_str = ''.join([('00000000' + bin(x)[2:])[-8:] for x in list(bit_str)])
    bit_str = univ.BitString("'%s'B" % bit_str)
    pubkeyid = univ.Sequence()
    pubkeyid.setComponentByPosition(0, univ.ObjectIdentifier('1.2.840.113549.1.1.1'))  # == OID for rsaEncryption
    pubkeyid.setComponentByPosition(1, univ.Null(''))
    pubkey_seq = univ.Sequence()
    pubkey_seq.setComponentByPosition(0, pubkeyid)
    pubkey_seq.setComponentByPosition(1, bit_str)
    pubkey = der_encoder.encode(pubkey_seq)
    return b'-----BEGIN PUBLIC KEY-----\n' + base64.encodebytes(pubkey) + b'-----END PUBLIC KEY-----\n'


def x509_time(**kwargs) -> bytes:
    dt = datetime.utcnow() + timedelta(**kwargs)
    return dt.strftime('%Y%m%d%H%M%SZ').encode('utf-8')


def make_cert(req: X509Req, ca_pkey: PKey) -> X509:
    cert = X509()
    cert.set_serial_number(1)
    cert.set_version(0)
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.set_notBefore(x509_time(minutes=-1))
    cert.set_notAfter(x509_time(days=30))
    ca_subj = cert.get_subject()
    ca_subj.CN = 'The YueChen'
    ca_subj.O = 'The Organization Otherwise Known as YueChen CA, Inc.'
    cert.set_issuer(ca_subj)
    cert.sign(ca_pkey, 'sha1')
    return cert


def make_req(pub_key, cn=None, digest=None) -> X509Req:
    req = X509Req()
    req.set_version(0)
    req.set_pubkey(pub_key)
    if cn is not None:
        subject = req.get_subject()
        subject.CN = cn.encode('utf-8')
    if digest:
        req.sign(pub_key, digest)
    return req


class AESCrypto(object):
    AES_CBC_IV = b'\x00' * 16

    @classmethod
    def cbc_encrypt(cls, data, key):
        if not isinstance(data, bytes):
            data = data.encode()

        cipher = Cipher(algorithms.AES(key),
                        modes.CBC(cls.AES_CBC_IV),
                        backend=default_backend())
        encryptor = cipher.encryptor()

        padded_data = encryptor.update(cls.pkcs7_padding(data))

        return padded_data

    @classmethod
    def cbc_decrypt(cls, data, key):
        if not isinstance(data, bytes):
            data = data.encode()

        cipher = Cipher(algorithms.AES(key),
                        modes.CBC(cls.AES_CBC_IV),
                        backend=default_backend())
        decryptor = cipher.decryptor()

        uppaded_data = cls.pkcs7_unpadding(decryptor.update(data))
        return uppaded_data

    @staticmethod
    def pkcs7_unpadding(padded_data):
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data)

        try:
            uppadded_data = data + unpadder.finalize()
        except ValueError:
            raise Exception('无效的加密信息!')
        else:
            return uppadded_data

    @staticmethod
    def pkcs7_padding(data):
        if not isinstance(data, bytes):
            data = data.encode()

        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        padded_data = padder.update(data) + padder.finalize()

        return padded_data
