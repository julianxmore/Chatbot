import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ====== CONFIG ======
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "mi_token_de_verificacion")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "REEMPLAZA_CON_TU_TOKEN")
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v20.0")

def send_whatsapp_text(phone_number_id: str, to: str, text: str):
    url = f"https://graph.facebook.com/{API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    r = requests.post(url, headers=headers, json=payload, timeout=15)
    print("Meta response:", r.status_code, r.text)
    return r.status_code, r.text

# ====== MENU ======
MENU = (
    "📚 1) Cancelación o aplazamiento de semestre\n"
    "📥 2) Reintegro a la universidad\n"
    "📝 3) Inscripción o cancelación de asignaturas\n"
    "🎓 4) Inscripción de trabajo de grado\n"
    "🗂️ 5) Permiso para RIUD\n"
    "📄 6) Actas de sustentación\n"
    "📑 7) Constancias de estudio o certificados de notas\n"
    "✉️ 8) Redactar correo al programa\n\n"
    "Responde con el número de la opción."
)

RESPUESTAS = {
    "1": (
        "🔄 Aplazamiento (semanas 1–2): correo a ingelectronica@udistrital.edu.co con carta de motivos y paz y salvo de Laboratorios, "
        "Bienestar y Biblioteca.\n"
        "❌ Cancelación (semanas 3–8): correo a secing@udistrital.edu.co con los mismos soportes.\n"
        "📌 La decisión final la toma el Consejo de Facultad."
    ),
    "2": (
        "🔁 Reintegro: consulta la página de Admisiones y compra el PIN de reintegro cuando esté habilitado. "
        "Suele publicarse ~2 meses antes de terminar el semestre y el PIN está disponible ~1.5 meses antes del cierre."
    ),
    "3": (
        "📅 Inscripción/cancelación de asignaturas:\n"
        "• Semana 1: trámite ante el Proyecto Curricular.\n"
        "• Semanas 2–3 aprox.: trámite ante el Consejo de Facultad.\n"
        "Revisa siempre el cronograma oficial."
    ),
    "4": (
        "🎓 Inscripción de trabajo de grado: solo por formularios publicados en las noticias de la Facultad de Ingeniería. "
        "Revisa el banner PDF con pasos y requisitos."
    ),
    "5": (
        "🗂️ RIUD (Repositorio): consulta las noticias del proyecto de Ingeniería Electrónica. "
        "Allí están los formularios y la guía paso a paso para subir al repositorio."
    ),
    "6": (
        "📄 Actas de sustentación: se solicitan por formulario (PDF). Completa y envía según las instrucciones del formato."
    ),
    "7": (
        "📑 Constancias/certificados: consulta valores en ‘Derechos pecuniarios’, paga y luego escribe a "
        "secingelectronica@udistrital.edu.co con copia a ingelectronica@udistrital.edu.co, incluyendo tus datos y el tipo de documento."
    ),
    "8": (
        "Asunto: Consulta sobre proceso académico\n\n"
        "Estimados señores,\n\n"
        "Solicito información sobre [tu caso]. Quedo atento(a) a requerimientos adicionales.\n\n"
        "Cordialmente,\n[Nombre]\n[Documento]\n[Código]\n[Programa]\n"
        "Enviar a: ingelectronica@udistrital.edu.co"
    )
}

# ====== WEBHOOK VERIFY (GET) ======
@app.get("/webhook")
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "forbidden", 403

# ====== WEBHOOK RECEIVE (POST) ======
@app.post("/webhook")
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    try:
        entry = data["entry"][0]
        change = entry["changes"][0]["value"]
        phone_number_id = change["metadata"]["phone_number_id"]
        messages = change.get("messages", [])
        if not messages:
            return "no messages", 200

        msg = messages[0]
        from_wa = msg["from"]  # user phone
        body = ""
        if msg.get("type") == "text":
            body = msg["text"].get("body", "").strip().lower()

        # Routing
        if body in ("hola", "menu", "hi", "buenas"):
            send_whatsapp_text(phone_number_id, from_wa, "¡Hola! Este es el menú:\n\n" + MENU)
        elif body in RESPUESTAS:
            send_whatsapp_text(phone_number_id, from_wa, RESPUESTAS[body])
            send_whatsapp_text(phone_number_id, from_wa, "¿Deseas volver al menú? Escribe: menu")
        else:
            send_whatsapp_text(phone_number_id, from_wa, "No entendí. Escribe 'menu' para ver opciones.")
    except Exception as e:
        print("Error procesando payload:", e)
    return "ok", 200

if __name__ == "__main__":
    # Puerto para Render/Heroku-style
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
