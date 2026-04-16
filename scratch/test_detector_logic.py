import sys
sys.path.insert(0, "/app")
from modules.services import department_detector

test_cases = [
    "SENA Santander fortalece cooperación internacional",
    "Emprendimiento en Manizales crece un 20%",
    "Nueva planta de energía en el Valle del Cauca",
    "Impacto tecnológico en Bogotá y Medellín",
    "Noticia nacional sobre el precio del dólar"
]

for title in test_cases:
    dept = department_detector.detect(title)
    print(f"Título: {title}")
    print(f"Detección: {dept}")
    print("-" * 20)
