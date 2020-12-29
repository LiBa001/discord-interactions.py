from nacl.signing import VerifyKey


def verify_key(raw_body: bytes, signature: str, timestamp: str, client_public_key: str) -> bool:
    message = timestamp.encode() + raw_body
    try:
        vk = VerifyKey(bytes.fromhex(client_public_key))
        vk.verify(message, bytes.fromhex(signature))
        return True
    except Exception as ex:
        print(ex)
    return False
