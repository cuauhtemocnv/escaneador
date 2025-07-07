import http.client
import json
import datetime
import re
import requests
import time  # Para poner la pausa entre ejecuciones

# --- CREDENCIALES ---
TELEGRAM_TOKEN = "7778298784:AAFCRSTlRVHaS3zzsLH_9HcJF3gd2F3mlHE"
CHAT_ID = 7437969496

TARGET_AIRLINES = ["Volaris", "Viva", "VB", "Y4"]

def get_flights_on_date(date_str):
    conn = http.client.HTTPSConnection("google-flights2.p.rapidapi.com")
    headers = {
        'x-rapidapi-key': "27b4f6e253msh7f835bce4fd0595p14f6aejsnc191fb96cbcb",
        'x-rapidapi-host': "google-flights2.p.rapidapi.com"
    }

    conn.request("GET", f"/api/v1/searchFlights?departure_id=GDL&arrival_id=LAP&outbound_date={date_str}&travel_class=ECONOMY&adults=1&show_hidden=1&currency=MXN&language_code=en-US&country_code=MX", headers=headers)
    res = conn.getresponse()
    data = res.read()
    flights_data = json.loads(data.decode("utf-8"))
    itineraries = flights_data.get("data", {}).get("itineraries", {})
    all_flights = itineraries.get("topFlights", []) + itineraries.get("otherFlights", [])

    results = []
    for flight in all_flights:
        flights = flight.get("flights", [])
        if not flights:
            continue
        airline_name = flights[0].get("airline", "")
        if not any(code in airline_name for code in TARGET_AIRLINES):
            continue

        total_minutes = flight.get("duration", {}).get("raw", "")
        raw_price = flight.get("price", "999999")

        try:
            if isinstance(raw_price, str):
                price = int(raw_price.replace(",", ""))
            else:
                price = int(raw_price)
        except (ValueError, TypeError):
            continue

        if total_minutes <= 120:
            results.append({
                "fecha": date_str,
                "aerolinea": airline_name,
                "salida": flight.get("departure_time"),
                "llegada": flight.get("arrival_time"),
                "duracion_min": total_minutes,
                "precio": price
            })
    return results

def buscar_mejor_vuelo():
    mejores = []
    for day in range(14, 22):
        date_str = f"2025-07-{day:02d}"
        vuelos = get_flights_on_date(date_str)
        mejores.extend(vuelos)

    if not mejores:
        return None

    mejores = sorted(mejores, key=lambda x: x["precio"])
    return mejores[0]

def enviar_mensaje_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": texto}
    response = requests.post(url, data=data)
    return response.status_code == 200

# --- EJECUCIÓN PROGRAMADA ---
def ejecutar_programa():
    while True:
        vuelo = buscar_mejor_vuelo()

        if vuelo and vuelo["precio"] < 2200:
            horas = vuelo["duracion_min"] // 60
            mins = vuelo["duracion_min"] % 60
            mensaje = (
                f"✈️ ¡Oferta encontrada!\n\n"
                f"📅 Fecha: {vuelo['fecha']}\n"
                f"🛫 Salida: {vuelo['salida']}\n"
                f"🛬 Llegada: {vuelo['llegada']}\n"
                f"🛩️ Aerolínea: {vuelo['aerolinea']}\n"
                f"⏱️ Duración: {horas}h {mins}min\n"
                f"💸 Precio: {vuelo['precio']} MXN"
            )
            enviar_mensaje_telegram(mensaje)
        else:
            print("No se encontró vuelo bajo 2000 MXN.")
        
        # Espera 8 horas (28,800 segundos)
        time.sleep(60)  # 8 horas = 28800 segundos
        break

# --- EJECUCIÓN DIRECTA ---
if __name__ == "__main__":
    ejecutar_programa()
