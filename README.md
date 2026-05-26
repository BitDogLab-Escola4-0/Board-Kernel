# BitDogLab Board Kernel

Firmware MicroPython para a placa **Raspberry Pi Pico 2W** com suporte a **WiFi (TCP)** e **Bluetooth (HC-05)** para controle de periféricos e execução remota de comandos.

## 📋 Visão Geral

O firmware implementa um sistema simples de execução de comandos que permite controlar a placa BitDogLab de forma remota via WiFi ou Bluetooth. 

**Características principais:**
- ✅ Servidor WiFi Access Point (AP) com TCP na porta 8080
- ✅ Comunicação Bluetooth via módulo HC-05 (UART)
- ✅ Suporte a LED RGB (PWM), NeoPixel 5x5 e Buzzers
- ✅ Interface unificada via GenericAPI
- ✅ Loop contínuo recebendo comandos de ambas as interfaces
- ✅ Sem feedback visual no OLED (console apenas)

---

## 🚀 Arquitetura

```
main.py                          ← Arquivo principal (inicialização + loop de comandos)
├── Inicializa GenericAPI
├── Cria Access Point WiFi
├── Inicia UART para Bluetooth
└── Loop infinito aguardando comandos

genericAPI/
├── genericAPI.py                ← Classe GenericAPI (periféricos)
├── config_pins.py               ← Configurações de pinos por versão
└── __init__.py

lib/
└── ssd1306.py                   ← Driver do display OLED (biblioteca)
```

---

## 🔧 Configuração de Hardware

### Conexões HC-05 (Bluetooth)

O módulo HC-05 deve estar conectado na **UART0** da placa:

```
HC-05 TX  → Pico RX  (GPIO1)
HC-05 RX  → Pico TX  (GPIO0)
HC-05 VCC → 3.3V ou 5V (conforme especificação)
HC-05 GND → GND
```

**Baudrate padrão:** 9600 bps

### Pinagem da Placa (BitDogLab v07)

| Componente        | Pino GPIO | Tipo   |
|-------------------|-----------|--------|
| LED RGB - Red     | 12        | PWM    |
| LED RGB - Green   | 13        | PWM    |
| LED RGB - Blue    | 11        | PWM    |
| Buzzer A          | 21        | PWM    |
| Buzzer B          | 10        | PWM    |
| NeoPixel Matrix   | 7         | Digital|
| Botão A           | 5         | Input  |
| Botão B           | 6         | Input  |
| Joystick Button   | 22        | Input  |
| Joystick VRx      | 26        | ADC    |
| Joystick VRy      | 27        | ADC    |
| Microfone         | 28        | ADC    |
| OLED SDA          | 2         | I2C    |
| OLED SCL          | 3         | I2C    |

---

## 📱 Interfaces de Conexão

### WiFi (TCP)

- **SSID:** `BDL #001`
- **Senha:** `BDL001`
- **IP da placa:** `192.168.4.1`
- **Porta TCP:** `8080`

**Exemplo de conexão e envio de comando (Python):**

```python
import socket

# Conectar ao servidor TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.4.1', 8080))

# Enviar comando
comando = "api.set_rgb(255, 0, 0)\n"
sock.send(comando.encode())

# Receber resposta
resposta = sock.recv(1024).decode()
print(f"Resposta: {resposta}")

sock.close()
```

### Bluetooth (HC-05)

- **Baudrate:** 9600
- **Terminador de comando:** `\r` ou `\n`

**Exemplo de envio via terminal serial:**

```
at 19200 baud

api.set_rgb(255, 0, 0)
[Enter]
```

---

## 💻 API de Comandos

Os comandos executados remotamente têm acesso ao objeto `api` (instância de `GenericAPI`).

### Controle de LED RGB

```python
# Definir cor (valores 0-255)
api.set_rgb(red, green, blue)

# Exemplos
api.set_rgb(255, 0, 0)      # Vermelho
api.set_rgb(0, 255, 0)      # Verde
api.set_rgb(0, 0, 255)      # Azul
api.set_rgb(0, 0, 0)        # Desligado
```

### Controle de Buzzer

```python
# Tocar frequência por tempo especificado
api.play_buzzer(frequencia_hz, duration_ms)

# Exemplos
api.play_buzzer(1000, 200)   # 1kHz por 200ms
api.play_buzzer(2000, 100)   # 2kHz por 100ms
api.play_buzzer(0, 0)        # Desligar
```

### Controle de NeoPixel

```python
# String format: "posição:r,g,b;posição:r,g,b;..."
api.set_neopixel("0:255,0,0;1:0,255,0;2:0,0,255")

# Apagar todos os LEDs
api.clear_matrix()

# Exemplos
api.set_neopixel("0:255,0,0")                    # LED 0 vermelho
api.set_neopixel("0:255,0,0;1:0,255,0;2:0,0,255") # 3 LEDs em cores diferentes
```

### Mapeamento do NeoPixel (5x5)

```
 0  1  2  3  4
 5  6  7  8  9
10 11 12 13 14
15 16 17 18 19
20 21 22 23 24
```

---

## ⚙️ Configuração do HC-05

### Mudando o Nome do Dispositivo

O módulo HC-05 por padrão aparece como "HC-05". Para mudar o nome:

1. **Entre no modo AT:**
   - Desconecte a alimentação
   - Pressione/segure o botão no módulo (ou conecte pino EN/KEY ao VCC)
   - Reconecte a alimentação mantendo o botão pressionado
   - O LED deve piscar lentamente (~2 segundos)

2. **Configure a UART para 38400 baud** (modo AT usa essa velocidade)

3. **Envie os comandos AT**:

   ```python
   # Verifica se está no modo AT
   uart.write('AT\r\n')  # Deve responder com "OK"

   # Muda o nome para "BitDogLab" (ou outro nome de sua escolha)
   uart.write('AT+NAME=BitDogLab\r\n')  # Deve responder com "OK"
   ```

4. **Reinicie o módulo**:
   - Desconecte a alimentação
   - Reconecte normalmente (sem pressionar o botão)
   - O módulo deve agora aparecer com o novo nome

### Outros Comandos AT Úteis

- `AT+PSWD=xxxx` - Muda a senha do módulo (padrão é 1234)
- `AT+UART=9600,0,0` - Configura baudrate para 9600
- `AT+VERSION?` - Mostra a versão do firmware
- `AT+ADDR?` - Mostra o endereço MAC do módulo

---

## 🎯 Fluxo de Execução

```
┌─────────────────────────────────────────┐
│      INICIALIZAÇÃO (main.py)            │
├─────────────────────────────────────────┤
│ 1. Importa GenericAPI                   │
│ 2. Inicializa periféricos (LED, PWM)    │
│ 3. Cria Access Point WiFi               │
│ 4. Inicia UART para Bluetooth           │
│ 5. Inicia servidor TCP                  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│      LOOP PRINCIPAL                     │
├─────────────────────────────────────────┤
│ ┌──────────────────────────────────┐   │
│ │ Verifica conexão TCP             │   │
│ │ (aguarda cliente em timeout=1s)  │   │
│ └──────────────────────────────────┘   │
│              ↓                          │
│ ┌──────────────────────────────────┐   │
│ │ Se cliente conectado:            │   │
│ │ Recebe dados (1024 bytes)        │   │
│ │ Processa comandos (terminador \n)   │   │
│ │ Executa com exec()               │   │
│ │ Retorna resposta (OK ou ERROR)   │   │
│ └──────────────────────────────────┘   │
│              ↓                          │
│ ┌──────────────────────────────────┐   │
│ │ Verifica dados Bluetooth         │   │
│ │ Recebe caractere por caractere   │   │
│ │ Processa comandos (terminador \n)   │   │
│ │ Executa com exec()               │   │
│ │ Retorna resposta (OK ou ERROR)   │   │
│ └──────────────────────────────────┘   │
│              ↓                          │
│ Aguarda 10ms e repete                  │
└─────────────────────────────────────────┘
```

---

## 📝 Exemplos de Uso

### Exemplo 1: Blink RGB via WiFi

```bash
# Terminal Linux/macOS
(echo "api.set_rgb(255, 0, 0)"; sleep 0.5; echo "api.set_rgb(0, 0, 0)") | nc -q 1 192.168.4.1 8080

# Resposta esperada:
# OK
# OK
```

### Exemplo 2: Ativar Buzzer via Bluetooth

Use um terminal serial como `miniterm.py`:

```bash
miniterm.py /dev/ttyUSB0 9600
```

Depois envie:
```
api.play_buzzer(1000, 500)
[Enter]
```

Resposta esperada: `OK`

### Exemplo 3: Padrão no NeoPixel via WiFi

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.4.1', 8080))

# Criar padrão de coração
comando = "api.set_neopixel('2:255,0,0;6:255,0,0;14:255,0,0;15:255,0,0;23:255,0,0;17:255,0,0;21:255,0,0;19:255,0,0;10:255,0,0;8:255,0,0')\n"
sock.send(comando.encode())

resposta = sock.recv(1024)
print(resposta.decode())

sock.close()
```

---

## 🔍 Debug e Logs

O sistema imprime informações de debug no console serial:

```
==================================================
BitDogLab - Iniciando...
==================================================
Inicializando periféricos...
✓ Periféricos inicializados
Inicializando Bluetooth HC-05...
✓ Bluetooth HC-05 pronto
Criando Access Point WiFi...
✓ WiFi AP criado: BDL #001 | IP: 192.168.4.1:8080
==================================================

>>> Sistema pronto para receber comandos <<<

[WiFi] Cliente conectado: ('192.168.4.5', 54321)
[WiFi] CMD: api.set_rgb(255, 0, 0) -> OK
[WiFi] Cliente desconectado

[BT] CMD: api.play_buzzer(1000, 200) -> OK
```

---

## ⚠️ Tratamento de Erros

Se um comando falhar, o sistema retorna uma mensagem de erro:

```
ERROR: [descrição do erro]
```

**Exemplos:**
```
ERROR: invalid syntax (<string>, line 1)
ERROR: 'GenericAPI' object has no attribute 'invalid_method'
ERROR: division by zero
```

---

## 🛠️ Modificação de Configurações

### Alterar SSID e Senha WiFi

Editar `main.py`:

```python
AP_SSID = "NOVO_SSID"
AP_PASSWORD = "NOVA_SENHA"
```

### Alterar Porta TCP

Editar `main.py`:

```python
TCP_PORT = 9000  # em vez de 8080
```

### Alterar Baudrate Bluetooth

Editar `main.py`:

```python
UART_BAUDRATE = 115200  # em vez de 9600
```

---

## 📦 Estrutura de Arquivos

```
Board-Kernel/
├── main.py                      # ★ Arquivo principal
├── hardware.py                  # (DEPRECATED) - Substituído por GenericAPI
├── wifi.py                      # (DEPRECATED) - Código movido para main.py
├── bluetooth_hc05.py            # (DEPRECATED) - Código movido para main.py
├── README.md                    # Esta documentação
├── config/
│   └── changeName-HC05.py       # Utilitário para configurar HC-05
├── firmware/
│   ├── BitDogLab.uf2           # Firmware para Pico 2W
│   ├── BitDogLab_W.uf2         # Firmware alternativo
│   └── clean.uf2               # Firmware para limpar placa
├── lib/
│   └── ssd1306.py              # Driver OLED
└── genericAPI/
    ├── __init__.py
    ├── genericAPI.py            # ★ API unificada
    └── config_pins.py           # Configurações de pinos
```

---

## 🚨 Resolução de Problemas

### Problema: "AP creation timeout"
**Causa:** WiFi não está ativando
**Solução:** Reinicie a placa ou verifique se o módulo WiFi está OK

### Problema: Comandos via WiFi não funcionam
**Causa:** Cliente não conectado corretamente
**Solução:** 
- Verifique o IP e porta: `192.168.4.1:8080`
- Confira se o comando termina com `\n`
- Veja os logs no console serial

### Problema: Bluetooth não recebe comandos
**Causa:** UART configurado com baudrate errado
**Solução:**
- Verifique se HC-05 está em 9600 baud
- Confira as conexões TX/RX
- Use terminal serial para testar

### Problema: "ERROR: invalid syntax"
**Causa:** Comando Python tem erro de sintaxe
**Solução:**
- Verifique a sintaxe do comando
- Não esqueça de importar módulos necessários
- Use `api.` para acessar a API

---

## 📚 Referências

- [MicroPython Documentação](https://docs.micropython.org/)
- [Raspberry Pi Pico 2W Datasheet](https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf)
- [HC-05 AT Commands](http://www.martyncurrey.com/arduino-hc-05-bluetooth-module-at-mode/)

---

**Última atualização:** Maio de 2026  
**Versão:** 2.0 (Refatoração)
