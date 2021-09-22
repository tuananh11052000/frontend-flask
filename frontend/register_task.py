from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
import hashlib
import binascii
import warnings
import json
import secp256k1

from sawtooth_signing.core import SigningError
from sawtooth_signing.core import ParseError

from sawtooth_signing.core import PrivateKey
from sawtooth_signing.core import PublicKey
from sawtooth_signing.core import Context

__CONTEXTBASE__ = secp256k1.Base(ctx=None, flags=secp256k1.ALL_FLAGS)
__CTX__ = __CONTEXTBASE__.ctx


class Secp256k1PrivateKey(PrivateKey):
    def __init__(self, secp256k1_private_key):
        self._private_key = secp256k1_private_key

    def get_algorithm_name(self):
        return "secp256k1"

    def as_hex(self):
        return binascii.hexlify(self.as_bytes()).decode()

    def as_bytes(self):
        return bytes(self._private_key.private_key)

    @property
    def secp256k1_private_key(self):
        return self._private_key

    @staticmethod
    def from_bytes(byte_str):
        return Secp256k1PrivateKey(secp256k1.PrivateKey(byte_str, ctx=__CTX__))

    @staticmethod
    def from_hex(hex_str):
        try:
            return Secp256k1PrivateKey.from_bytes(binascii.unhexlify(hex_str))
        except Exception as e:
            raise ParseError('Unable to parse hex private key: {}'.format(
                e)) from e

    @staticmethod
    def new_random():
        return Secp256k1PrivateKey(secp256k1.PrivateKey(ctx=__CTX__))


class Secp256k1PublicKey(PublicKey):
    def __init__(self, secp256k1_public_key):
        self._public_key = secp256k1_public_key

    @property
    def secp256k1_public_key(self):
        return self._public_key

    def get_algorithm_name(self):
        return "secp256k1"

    def as_hex(self):
        return binascii.hexlify(self.as_bytes()).decode()

    def as_bytes(self):
        with warnings.catch_warnings():  # squelch secp256k1 warning
            warnings.simplefilter('ignore')
            return self._public_key.serialize()

    @staticmethod
    def from_bytes(byte_str):
        public_key = secp256k1.PublicKey(byte_str, raw=True, ctx=__CTX__)
        return Secp256k1PublicKey(public_key)

    @staticmethod
    def from_hex(hex_str):
        try:
            return Secp256k1PublicKey.from_bytes(binascii.unhexlify(hex_str))
        except Exception as e:
            raise ParseError('Unable to parse hex public key: {}'.format(
                e)) from e


class Secp256k1Context(Context):
    def __init__(self):
        self._ctx = __CTX__

    def get_algorithm_name(self):
        return "secp256k1"

    def sign(self, message, private_key):
        try:
            signature = private_key.secp256k1_private_key.ecdsa_sign(message)
            signature = private_key.secp256k1_private_key \
                .ecdsa_serialize_compact(signature)

            return signature.hex()
        except Exception as e:
            raise SigningError('Unable to sign message: {}'.format(
                str(e))) from e

    def verify(self, signature, message, public_key):
        try:
            if isinstance(signature, str):
                signature = bytes.fromhex(signature)

            sig = public_key.secp256k1_public_key.ecdsa_deserialize_compact(
                signature)
            return public_key.secp256k1_public_key.ecdsa_verify(message, sig)
        # pylint: disable=broad-except
        except Exception:
            return False

    def new_random_private_key(self):
        return Secp256k1PrivateKey.new_random()

    def get_public_key(self, private_key):
        return Secp256k1PublicKey(private_key.secp256k1_private_key.pubkey)


def submit_transaction(private_key_hex, hardware_description, dataset_description, task_id):
    private_key_bytes = binascii.unhexlify(private_key_hex)
    private_key_ = secp256k1.PrivateKey(private_key_bytes, ctx=__CTX__)
    private_key = Secp256k1PrivateKey(private_key_)
    print(private_key.as_hex())
    # Tao khoa
    context = create_context('secp256k1')
    signer = CryptoFactory(context).new_signer(private_key)
    # -------------------------------------------------------
    # Ma hoa payload
    print(signer.get_public_key().as_hex())
    import cbor

    payload = {
        'public_key': signer.get_public_key().as_hex(),
        'task_id': task_id,
        'hardware_description': hardware_description,
        'dataset_description': dataset_description
    }

    payload_bytes = cbor.dumps(payload)
    # ------------------------------------------------------------
    # Tao Transaction
    from hashlib import sha512
    from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
    # Tao transaction header
    # xac dinh dia chi input output
    address = hashlib.sha512('registertask'.encode("utf-8")).hexdigest(
    )[0:6] + hashlib.sha512(payload['public_key'].encode('utf-8')).hexdigest()[:64]

    txn_header_bytes = TransactionHeader(
        family_name='register_task',
        family_version='1.0',
        inputs=[str(address)],
        outputs=[str(address)],
        signer_public_key=signer.get_public_key().as_hex(),
        batcher_public_key=signer.get_public_key().as_hex(),
        dependencies=[],
        payload_sha512=sha512(payload_bytes).hexdigest()
    ).SerializeToString()
    # Tao transaction
    from sawtooth_sdk.protobuf.transaction_pb2 import Transaction

    signature = signer.sign(txn_header_bytes)

    txn = Transaction(
        header=txn_header_bytes,
        header_signature=signature,
        payload=payload_bytes
    )
    # Ma hoa transaction
    from sawtooth_sdk.protobuf.transaction_pb2 import TransactionList

    txn_list_bytes = TransactionList(
        transactions=[txn]
    ).SerializeToString()

    # --------------------------------------------------------
    # Tao batch
    # Batch header
    from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader

    txns = [txn]

    batch_header_bytes = BatchHeader(
        signer_public_key=signer.get_public_key().as_hex(),
        transaction_ids=[txn.header_signature for txn in txns],
    ).SerializeToString()
    # Tao batch
    from sawtooth_sdk.protobuf.batch_pb2 import Batch

    signature = signer.sign(batch_header_bytes)

    batch = Batch(
        header=batch_header_bytes,
        header_signature=signature,
        transactions=txns
    )
    # ma hoa batch
    from sawtooth_sdk.protobuf.batch_pb2 import BatchList

    batch_list_bytes = BatchList(batches=[batch]).SerializeToString()

    # -------------------------------------------------------------------
    # Submit transaction
    import urllib.request
    from urllib.error import HTTPError

    try:
        print(payload_bytes)
        request = urllib.request.Request(
            'http://172.18.0.5:8008/batches',
            batch_list_bytes,
            method='POST',
            headers={'Content-Type': 'application/octet-stream'})
        urllib.request.urlopen(request)
    except HTTPError as e:
        response = e.file
