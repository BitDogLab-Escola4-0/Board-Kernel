### Board-Kernel

# Firmware UF2

# Generic API

# Libraries

# Código da Placa BitDogLab

Este é o código que deve ser carregado na placa para permitir a comunicação via Bluetooth com o aplicativo BitDogLab.

## 📋 Visão Geral

O código implementa um interpretador MicroPython simples que:

1. Configura a comunicação UART para o módulo HC-05
2. Recebe comandos via Bluetooth
3. Executa os comandos recebidos
4. Retorna o resultado da execução

## 🛠️ Configuração do Módulo HC-05

### Mudando o Nome do Dispositivo Bluetooth

Por padrão, o módulo HC-05 aparece como "HC-05" na lista de dispositivos Bluetooth. Para mudar este nome:

1. **Entre no modo AT**:

   - Desconecte a alimentação do HC-05
   - Pressione e segure o botão no módulo HC-05 (ou conecte o pino EN/KEY ao VCC)
   - Reconecte a alimentação enquanto mantém o botão pressionado
   - O LED deve piscar lentamente (cerca de 2 segundos entre piscadas)

2. **Conecte o módulo à placa**:

   ```
   HC-05    Placa
   TX   →   RX
   RX   →   TX
   VCC  →   3.3V/5V
   GND  →   GND
   ```

3. **Configure a UART para 38400 baud** (o modo AT usa esta velocidade):

   ```python
   uart = UART(0, baudrate=38400)
   uart.init(38400, bits=8, parity=None, stop=1)
   ```

4. **Envie os comandos AT**:

   ```python
   # Verifica se está no modo AT
   uart.write('AT\r\n')  # Deve responder com "OK"

   # Muda o nome para "BitDogLab" (ou outro nome de sua escolha)
   uart.write('AT+NAME=BitDogLab\r\n')  # Deve responder com "OK"
   ```

5. **Reinicie o módulo**:
   - Desconecte a alimentação
   - Reconecte normalmente (sem pressionar o botão)
   - O módulo deve agora aparecer com o novo nome

### Outros Comandos AT Úteis

- `AT+PSWD=xxxx` - Muda a senha do módulo (padrão é 1234)
- `AT+UART=9600,0,0` - Configura baudrate para 9600
- `AT+VERSION?` - Mostra a versão do firmware
- `AT+ADDR?` - Mostra o endereço MAC do módulo

**Nota**: Depois de fazer as configurações, lembre-se de voltar o código para baudrate 9600 para operação normal.

## 🔧 Configuração do Hardware

### Conexão do HC-05

O módulo Bluetooth HC-05 deve ser conectado à UART0 da placa:

- TX do HC-05 → RX da placa
- RX do HC-05 → TX da placa
- VCC do HC-05 → 3.3V ou 5V (conforme especificação do seu módulo)
- GND do HC-05 → GND

### Configurações da UART

```python
uart = UART(0, baudrate=9600)
uart.init(9600, bits=8, parity=None, stop=1)
```
