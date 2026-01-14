import sys
import json
from typing import List, Dict

# =============== CONFIG GEMINI ===============
API_KEY = "AIzaSyD5Yk9GquqgT2mUDeTsCblGgUiZgn3nHO0"

MODEL  = "gemini-2.5-pro" #ejemplo utilizado

# =============== ESTILOS / CONSTANTES ===============
APP_BG  = "#0f172a"
FG1     = "#e2e8f0"
FG2     = "#cbd5e1"
PRIMARY = "#4d74c6"

# Chat estilo
LEFT_BG   = "#ffffff"   # globo profesor
RIGHT_BG  = "#c7f9cc"   # globo pepito
LEFT_FG   = "#1f2937"
RIGHT_FG  = "#0f3d1e"

PROFESOR = "Profesora"
PEPITO   = "Pepito"

# Rutas de las imágenes de los avatares
PROFESORA_AVATAR = "img/profesora_avatar.png"
PROFESORA        = "img/profesora.png"
PEPITO_AVATAR    = "img/alumno_avatar.png"
ALUMNO           = "img/alumno.png"
BIENVENIDA       = "img/bienvenida.png"

# =============== CARGA DE CONCEPTOS DESDE JSON ===============
def cargar_conceptos(path: str = "actividades.json") -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("actividades.json debe contener una lista de conceptos.")
        # Garantizamos que cada concepto tenga al menos un título
        for i, c in enumerate(data):
            if "titulo" not in c:
                c["titulo"] = f"Concepto {i+1}"
        return data
    except Exception as e:
        print(f"Error al cargar {path}: {e}", file=sys.stderr)
        return []


CONCEPTOS: List[Dict] = cargar_conceptos()
