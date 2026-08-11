"""
Implementação mínima de servidor WebSocket (RFC 6455) para MicroPython.

Não depende de nenhuma lib externa — só usa uhashlib (sha1) e ubinascii
(base64), que já vêm no MicroPython padrão do Pico W.

Cobre exatamente o que a gente precisa para falar com o WifiProvider.ts
do app (que usa a WebSocket API padrão do navegador/JS):
  - handshake HTTP -> 101 Switching Protocols
  - leitura de frames de texto (unmask, porque cliente sempre manda mascarado)
  - envio de frames de texto (sem mask, porque servidor nunca mascara)
  - resposta ao frame de close
"""

import uhashlib
import ubinascii

WS_MAGIC = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OPCODE_TEXT = 0x1
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


def _compute_accept_key(client_key: str) -> str:
    sha1 = uhashlib.sha1()
    sha1.update(client_key.encode() + WS_MAGIC)
    digest = sha1.digest()
    return ubinascii.b2a_base64(digest).decode().strip()


def _recv_exact(client_socket, n):
    """Lê exatamente n bytes do socket (ou None se a conexão cair)."""
    data = b""
    while len(data) < n:
        chunk = client_socket.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def _read_http_request(client_socket):
    """Lê a requisição HTTP crua até encontrar o fim dos headers (\\r\\n\\r\\n)."""
    request = b""
    while b"\r\n\r\n" not in request:
        chunk = client_socket.recv(256)
        if not chunk:
            break
        request += chunk
    return request


def _parse_headers(raw_request: bytes) -> dict:
    headers = {}
    text = raw_request.decode("utf-8", "ignore")
    for line in text.split("\r\n")[1:]:
        if ":" in line:
            key, _, value = line.partition(":")
            headers[key.strip().lower()] = value.strip()
    return headers


def perform_handshake(client_socket) -> bool:
    """
    Lê a requisição HTTP de upgrade e completa o handshake WebSocket.
    Retorna True se deu certo, False se não era uma requisição WS válida
    (nesse caso a conexão deve ser fechada pelo chamador).
    """
    raw_request = _read_http_request(client_socket)
    if not raw_request:
        return False

    headers = _parse_headers(raw_request)
    client_key = headers.get("sec-websocket-key")
    if not client_key:
        return False

    accept_key = _compute_accept_key(client_key)
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        "Sec-WebSocket-Accept: {}\r\n"
        "\r\n"
    ).format(accept_key)

    client_socket.send(response.encode())
    return True


def recv_frame(client_socket):
    """
    Lê um frame do cliente.
    Retorna (opcode, payload) onde payload é str para frames de texto,
    ou (None, None) se a conexão foi fechada/erro de leitura.
    """
    header = _recv_exact(client_socket, 2)
    if not header:
        return None, None

    b1, b2 = header[0], header[1]
    opcode = b1 & 0x0F
    masked = (b2 & 0x80) != 0
    length = b2 & 0x7F

    if length == 126:
        ext = _recv_exact(client_socket, 2)
        if ext is None:
            return None, None
        length = (ext[0] << 8) | ext[1]
    elif length == 127:
        ext = _recv_exact(client_socket, 8)
        if ext is None:
            return None, None
        length = 0
        for byte in ext:
            length = (length << 8) | byte

    mask_key = None
    if masked:
        mask_key = _recv_exact(client_socket, 4)
        if mask_key is None:
            return None, None

    payload = b""
    if length:
        payload = _recv_exact(client_socket, length)
        if payload is None:
            return None, None

    if masked and payload:
        payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

    if opcode == OPCODE_CLOSE:
        return OPCODE_CLOSE, None
    if opcode == OPCODE_TEXT:
        return OPCODE_TEXT, payload.decode("utf-8", "ignore")
    if opcode == OPCODE_PING:
        return OPCODE_PING, payload

    # opcodes binários/continuação não são usados pelo WifiProvider.ts hoje
    return opcode, payload


def send_text(client_socket, text: str):
    """Envia um frame de texto. Frames de servidor->cliente NUNCA são mascarados."""
    payload = text.encode("utf-8")
    length = len(payload)

    if length <= 125:
        header = bytes([0x81, length])
    elif length <= 65535:
        header = bytes([0x81, 126, (length >> 8) & 0xFF, length & 0xFF])
    else:
        header = bytes([0x81, 127]) + length.to_bytes(8, "big")

    client_socket.send(header + payload)


def send_pong(client_socket, payload=b""):
    length = len(payload)
    header = bytes([0x8A, length])
    client_socket.send(header + payload)


def send_close(client_socket):
    try:
        client_socket.send(bytes([0x88, 0x00]))
    except Exception:
        pass
