"""
BitDogLab Main Controller
Gerencia WiFi e Bluetooth simultaneamente recebendo e executando comandos
"""

import time
import gc
import network
import socket
from machine import UART, Pin

# Import GenericAPI para periféricos
from genericAPI import GenericAPI

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# WiFi Access Point
AP_SSID = "BDL #001"
AP_PASSWORD = "BDL001"
AP_IP = "192.168.4.1"
TCP_PORT = 8080

# Bluetooth HC-05 UART
UART_BAUDRATE = 9600

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

print("=" * 50)
print("BitDogLab - Iniciando...")
print("=" * 50)

# Inicializa GenericAPI (periféricos)
print("Inicializando periféricos...")
api = GenericAPI(version_key="bitdoglab_v07")
print("✓ Periféricos inicializados")

# Inicializa UART para Bluetooth HC-05
print("Inicializando Bluetooth HC-05...")
uart = UART(0, baudrate=UART_BAUDRATE)
uart.init(UART_BAUDRATE, bits=8, parity=None, stop=1)
print("✓ Bluetooth HC-05 pronto")

# Inicializa WiFi Access Point
print("Criando Access Point WiFi...")
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=AP_SSID, password=AP_PASSWORD)
ap.ifconfig((AP_IP, '255.255.255.0', AP_IP, AP_IP))

# Aguarda ativação do AP com timeout
timeout = 10
start = time.time()
while not ap.active():
    if time.time() - start > timeout:
        print("✗ Falha ao criar Access Point")
        break
    time.sleep(0.1)

print(f"✓ WiFi AP criado: {AP_SSID} | IP: {AP_IP}:{TCP_PORT}")
print("=" * 50)

# ============================================================================
# FUNÇÕES DE PROCESSAMENTO DE COMANDOS
# ============================================================================

def execute_command(command_str):
    """Executa um comando recebido"""
    command_str = command_str.strip()
    if not command_str:
        return None
    
    try:
        # Executa o comando no contexto global
        exec(command_str, {"api": api})
        return "OK"
    except Exception as e:
        return f"ERROR: {str(e)}"


def send_response(socket_obj, response):
    """Envia resposta via TCP"""
    try:
        socket_obj.send((response + "\n").encode())
    except:
        pass


def send_uart_response(response):
    """Envia resposta via UART"""
    try:
        uart.write((response + "\r\n").encode())
    except:
        pass

# ============================================================================
# SERVIDOR TCP (WiFi)
# ============================================================================

def start_tcp_server():
    """Inicia servidor TCP para conexões WiFi"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', TCP_PORT))
    server_socket.listen(1)
    
    print(f"Servidor TCP aguardando conexões em {AP_IP}:{TCP_PORT}")
    
    return server_socket


# ============================================================================
# LOOP PRINCIPAL
# ============================================================================

def main():
    """Loop principal - recebe comandos de WiFi e Bluetooth"""
    
    # Inicia servidor TCP
    server_socket = start_tcp_server()
    server_socket.settimeout(1)  # Non-blocking com timeout
    
    # Buffer para comandos Bluetooth
    bt_buffer = ""
    
    # Cliente TCP ativo (se houver)
    active_client = None
    
    print("\n>>> Sistema pronto para receber comandos <<<\n")
    
    try:
        while True:
            # ========== VERIFICA CONEXÃO TCP ==========
            if active_client is None:
                try:
                    active_client, client_addr = server_socket.accept()
                    print(f"[WiFi] Cliente conectado: {client_addr}")
                    active_client.settimeout(30)
                except OSError:
                    pass
                except Exception as e:
                    print(f"[WiFi] Erro na conexão: {e}")
                    active_client = None
            
            # ========== PROCESSA COMANDOS TCP ==========
            if active_client:
                try:
                    data = active_client.recv(1024)
                    if not data:
                        print("[WiFi] Cliente desconectado")
                        active_client.close()
                        active_client = None
                        gc.collect()
                    else:
                        # Processa cada comando terminado com \n
                        text = data.decode('utf-8', 'ignore')
                        for char in text:
                            if char in ('\n', '\r'):
                                if bt_buffer.strip():
                                    response = execute_command(bt_buffer)
                                    print(f"[WiFi] CMD: {bt_buffer[:50]} -> {response}")
                                    send_response(active_client, response)
                                    bt_buffer = ""
                            else:
                                bt_buffer += char
                except OSError:
                    pass
                except Exception as e:
                    print(f"[WiFi] Erro na comunicação: {e}")
                    active_client.close()
                    active_client = None
                    gc.collect()
            
            # ========== PROCESSA COMANDOS BLUETOOTH ==========
            if uart.any():
                try:
                    char = uart.read(1).decode('utf-8')
                    if char in ('\n', '\r'):
                        if bt_buffer.strip():
                            response = execute_command(bt_buffer)
                            print(f"[BT] CMD: {bt_buffer[:50]} -> {response}")
                            send_uart_response(response)
                        bt_buffer = ""
                    else:
                        bt_buffer += char
                except Exception as e:
                    print(f"[BT] Erro: {e}")
                    bt_buffer = ""
            
            # Pequena pausa para não sobrecarregar
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\n[MAIN] Interrompido pelo usuário")
    except Exception as e:
        print(f"\n[MAIN] Erro fatal: {e}")
    finally:
        if active_client:
            active_client.close()
        server_socket.close()
        print("[MAIN] Servidor finalizado")


# ============================================================================
# EXECUÇÃO
# ============================================================================

if __name__ == "__main__":
    main()
