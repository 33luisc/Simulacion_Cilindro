import math

# ==========================================
# MEDIDAS REALES (Centímetros cm)
# ==========================================
D_c = 18.40   # Diámetro del vaso (cm)
H_c = 30.00   # Altura del vaso (cm)
d_e = 5.88    # Diámetro de las pelotas (cm)

R_c = D_c / 2.0  # Radio del vaso (9.20 cm)
r_e = d_e / 2.0  # Radio de la pelota (2.94 cm)

# Volúmenes teóricos (cm^3)
VOLUMEN_VASO = math.pi * (R_c**2) * H_c
VOLUMEN_PELOTA = (4.0 / 3.0) * math.pi * (r_e**3)

# Parámetros físicos
GRAVEDAD = -981.0     # cm/s^2
RESTITUCION = 0.25    # Amortiguación de rebote
FRICCION_PISO = 0.70  # Ficción al rodar