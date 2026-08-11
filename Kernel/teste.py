from genericAPI.genericAPI import GenericAPI

# 1. Instancia a API (
bitdoglab = GenericAPI("bitdoglab_v07")

# Ligar LED RGB em Vermelho (Max u16)
bitdoglab.set_rgb(255, 0, 0)

# Tocar um 'Beep'
bitdoglab.play_buzzer(440, 100) # Nota Lá

# Acender o LED central da matriz em Verde (RGB 0-255)
bitdoglab.set_neopixel("12:0,255,0")
