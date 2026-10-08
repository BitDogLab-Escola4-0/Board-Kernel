import machine
import neopixel
import time
from machine import Pin, PWM
from .config_pins import VERSIONS

class GenericAPI:
    def __init__(self, version_key="bitdoglab_v07"):
        if version_key not in VERSIONS:
            raise ValueError(f"Versao {version_key} nao cadastrada.")
        
        self.config = VERSIONS[version_key]
        self._init_components()

    def _init_components(self):
        """Inicializa todos os periféricos com base no dicionário de pinos."""
        
        # --- LED RGB ---
        rgb = self.config["led_rgb"]
        self.led_r = PWM(Pin(rgb["r"]))
        self.led_g = PWM(Pin(rgb["g"]))
        self.led_b = PWM(Pin(rgb["b"]))
        # Frequência padrão para evitar cintilação
        for led in [self.led_r, self.led_g, self.led_b]:
            led.freq(1000)
            led.duty_u16(0)

        # --- BUZZER ---
        self.buzzer = PWM(Pin(self.config["buzzer"]["pin"]))
        self.buzzer.duty_u16(0)

        # --- MATRIZ NEOPIXEL ---
        m = self.config["matrix"]
        self.matrix = neopixel.NeoPixel(Pin(m["pin"]), m["num_leds"])
        self.matrix_size = m["num_leds"]

    # --- CONTROLES DO LED RGB ---
    def set_rgb(self, r, g, b):
        """
        Define a cor do LED RGB. Espera valores de 0 a 255 para r, g e b.
        Multiplicamos por 257 para escalar perfeitamente para 0-65535.
        """
        self.led_r.duty_u16(int(r * 257))
        self.led_g.duty_u16(int(g * 257))
        self.led_b.duty_u16(int(b * 257))

    # --- CONTROLES DO BUZZER ---
    def play_buzzer(self, freq, duration_ms=200):
        """Toca uma frequência específica."""
        if freq > 0:
            self.buzzer.freq(freq)
            self.buzzer.duty_u16(32768) # 50% de volume
            time.sleep_ms(duration_ms)
            self.buzzer.duty_u16(0)

    # --- FUNÇÕES AUXILIARES DA MATRIZ ---
    def map_numbers(self, pos, cols=5):
        """
        Mapeia um índice lógico (leitura padrão da esquerda para a direita)
        para o índice físico de uma matriz ligada em zigue-zague.
        Assumimos por padrão 5 colunas (matriz 5x5 da BitDogLab).
        """
        if pos < 0 or pos >= self.matrix_size:
            return pos # Retorna a própria posição se estiver fora do limite
            
        row = pos // cols # Descobre em qual linha estamos
        col = pos % cols  # Descobre em qual coluna estamos
        
        # Na BitDogLab, as linhas pares (0, 2, 4...) correm no sentido inverso
        if row % 2 == 0:
            col = (cols - 1) - col
            
        return (row * cols) + col

    # --- CONTROLES DA MATRIZ NEOPIXEL ---
    def set_neopixel(self, instruction_string):
        """
        Processa uma string no formato 'pos:r,g,b;pos:r,g,b'
        Exemplo: "0:255,0,0;12:0,255,0"
        """
        # 1. Limpa a matriz antes de começar o novo desenho
        self.clear_matrix() 
        
        # 2. Divide a string em instruções individuais
        instructions = instruction_string.split(';')
        
        for instruction in instructions:
            if not instruction.strip():
                continue
                
            try:
                # Separa posição e cores
                pos_str, cor_str = instruction.split(':')
                
                # Converte e mapeia a posição usando o novo método
                pos = int(pos_str)
                mapped_pos = self.map_numbers(pos, cols=5) 
                
                # Converte a string de cor "R,G,B" em uma tupla de inteiros
                color = tuple(map(int, cor_str.split(',')))
                
                # 3. Define a cor na memória
                if 0 <= mapped_pos < self.matrix_size:
                    self.matrix[mapped_pos] = color
                else:
                    print(f"Posição {mapped_pos} fora do range.")
                    
            except (ValueError, IndexError) as e:
                print(f"Erro ao processar '{instruction}': {e}")

        # 4. Atualiza o hardware uma única vez após processar toda a string
        self.matrix.write()

    def clear_matrix(self, update=True):
        for i in range(self.matrix_size):
            self.matrix[i] = (0, 0, 0)
        if update:
            self.matrix.write()
