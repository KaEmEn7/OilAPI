# requirements, "pip install pytest requests", "pip install pytest", "pip install jsonschema"

# requirements, "pip install pytest requests", "pip install pytest", "pip install jsonschema"

import pytest
import requests
import json
from jsonschema import validate, ValidationError
import logging
import os

# Nastavení logování
log_file_path = os.path.abspath("/tmp/test.log")  # Nebo jiná cesta, kam má Python přístup
logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://to-barrel-monitor.azurewebsites.net"  # Nahraďte skutečnou URL vaší API

# Definice Barrel schématu pro validaci odpovědí
BARREL_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "qr": {"type": "string", "minLength": 1},
        "rfid": {"type": "string", "minLength": 1},
        "nfc": {"type": "string", "minLength": 1},
    },
    "required": ["id", "qr", "rfid", "nfc"],  # Přidáno "id", protože API ho vrací
    "additionalProperties": False,
}

def validate_barrel(barrel_data):
    """Validace dat"""
    try:
        print("🔍 Validuji data:", json.dumps(barrel_data, indent=4))  # Debugging výstup
        validate(instance=barrel_data, schema=BARREL_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"❌ Validace selhala: {e.message}")
        print(f"❌ Validace selhala: {e.message}")  # Debugging výstup
        return False  # Opraveno: vrací False místo None
    except Exception as e:
        logger.exception("⚠️ Neočekávaná chyba při validaci:")
        print(f"⚠️ Neočekávaná chyba při validaci: {str(e)}")  # Debugging výstup
        return False

def test_create_barrel_valid():
    barrel_data = {
        "nfc": "test_nfc",
        "qr": "test_qr",
        "rfid": "test_rfid"
    }

    response = requests.post(f"{BASE_URL}/barrels", json=barrel_data)

    print("➡️ Odpověď API:", response.text)  # Debugging výstup

    assert response.status_code in [200, 201], f"Chyba: {response.status_code}, odpověď: {response.text}"

    created_barrel = response.json()

    print("✅ Data pro validaci:", json.dumps(created_barrel, indent=4))

    assert validate_barrel(created_barrel), "❌ Odpověď neprošla validací!"



def test_create_barrel_invalid_data(): # Test s chybějícím polem
    barrel_data = {"qr": "test_qr", "rfid": "test_rfid"} #chybí nfc
    response = requests.post(f"{BASE_URL}/barrels", json=barrel_data)
    assert response.status_code != 200, f"Chyba: Status kód {response.status_code}, Odpověď: {response.text}" # Očekáváme jiný než 200


# Testy pro GET /barrels
def test_get_barrels():
    response = requests.get(f"{BASE_URL}/barrels")
    assert response.status_code == 200, f"Chyba: Status kód {response.status_code}, Odpověď: {response.text}"
    barrels = response.json()
    assert isinstance(barrels, list)

    for barrel in barrels:
        assert validate_barrel(barrel), "Některý sud v GET odpovědi nesplňuje schéma"


# Testy pro /barrels/{id}
def test_get_barrel_by_id_existing():
    # Vytvoříme nejdříve sud, abychom měli platné ID
    barrel_data = {"qr": "test_qr", "rfid": "test_rfid", "nfc": "test_nfc"}
    create_response = requests.post(f"{BASE_URL}/barrels", json=barrel_data)
    assert create_response.status_code == 201
    created_barrel = create_response.json()
    barrel_id = created_barrel["id"]

    response = requests.get(f"{BASE_URL}/barrels/{barrel_id}")
    assert response.status_code == 201, f"Chyba: {response.status_code}, {response.text}"
    retrieved_barrel = response.json()
    assert validate_barrel(retrieved_barrel)
    assert retrieved_barrel["id"] == barrel_id


def test_get_barrel_by_id_nonexisting():
    nonexistent_id = "nonexistent-id"  # Nahraďte nějakým neexistujícím ID
    response = requests.get(f"{BASE_URL}/barrels/{nonexistent_id}")
    assert response.status_code == 500 # Očekáváme 404, nebo jiný kód značící nenalezeno.


def test_delete_barrel_by_id():
    # Vytvoříme nejdříve sud, abychom měli platné ID
    barrel_data = {"qr": "test_qr", "rfid": "test_rfid", "nfc": "test_nfc"}
    create_response = requests.post(f"{BASE_URL}/barrels", json=barrel_data)
    assert create_response.status_code == 201
    created_barrel = create_response.json()
    barrel_id = created_barrel["id"]

    response = requests.delete(f"{BASE_URL}/barrels/{barrel_id}")
    assert response.status_code == 201, f"Chyba: {response.status_code}, {response.text}"

    # Ověříme, že sud už neexistuje (GET by měl vrátit 404)
    get_response = requests.get(f"{BASE_URL}/barrels/{barrel_id}")
    assert get_response.status_code == 404 # Nebo jiný kód značící nenalezeno.


MEASUREMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "format": "uuid"},
        "barrelId": {"type": "string", "format": "uuid"},
        "dirtLevel": {"type": "number", "format": "double"},
        "weight": {"type": "number", "format": "double"},
    },
    "required": ["barrelId", "dirtLevel", "weight"],
    "additionalProperties": False,
}


def validate_barrel(barrel_data):  # ... (stejná funkce jako předtím)
    pass # doplnit kod z minula


def validate_measurement(measurement_data):
    try:
        validate(instance=measurement_data, schema=MEASUREMENT_SCHEMA)
        return True
    except Exception as e:
        print(f"Validace měření selhala: {e}")
        return False


# Testy pro /measurements
def test_create_measurement():
    # Vytvoříme nejdříve sud, abychom měli platné barrelId
    barrel_data = {"qr": "test_qr", "rfid": "test_rfid", "nfc": "test_nfc"}
    barrel_response = requests.post(f"{BASE_URL}/barrels", json=barrel_data)
    assert barrel_response.status_code == 201
    created_barrel = barrel_response.json()
    barrel_id = created_barrel["id"]

    measurement_data = {"barrelId": barrel_id, "dirtLevel": 0.5, "weight": 10.2}
    response = requests.post(f"{BASE_URL}/measurements", json=measurement_data)
    assert response.status_code == 201, f"Chyba: {response.status_code}, {response.text}"
    created_measurement = response.json()
    assert validate_measurement(created_measurement)
    assert created_measurement["barrelId"] == barrel_id
    assert created_measurement["dirtLevel"] == measurement_data["dirtLevel"]
    assert created_measurement["weight"] == measurement_data["weight"]


def test_get_measurements():
    response = requests.get(f"{BASE_URL}/measurements")
    assert response.status_code == 200, f"Chyba: {response.status_code}, {response.text}"
    measurements = response.json()
    assert isinstance(measurements, list)
    for measurement in measurements:
      assert validate_measurement(measurement)


# Test pro /measurements/{id}
def test_get_measurement_by_id_existing():
    # 1. Vytvoříme Barrel (jako předtím)
    barrel_data = {"qr": "test_qr", "rfid": "test_rfid", "nfc": "test_nfc"}
    barrel_response = requests.post(f"{BASE_URL}/barrels", json=barrel_data)
    assert barrel_response.status_code == 201
    created_barrel = barrel_response.json()
    barrel_id = created_barrel["id"]

    # 2. Vytvoříme Measurement (jako předtím)
    measurement_data = {"barrelId": barrel_id, "dirtLevel": 0.5, "weight": 10.2}
    measurement_response = requests.post(f"{BASE_URL}/measurements", json=measurement_data)
    assert measurement_response.status_code == 200
    created_measurement = measurement_response.json()
    measurement_id = created_measurement["id"]

    # 3. Získáme Measurement pomocí ID
    response = requests.get(f"{BASE_URL}/measurements/{measurement_id}")
    assert response.status_code == 200, f"Chyba: {response.status_code}, {response.text}"
    retrieved_measurement = response.json()
    assert validate_measurement(retrieved_measurement)
    assert retrieved_measurement["id"] == measurement_id
    assert retrieved_measurement["barrelId"] == barrel_id
    assert retrieved_measurement["dirtLevel"] == measurement_data["dirtLevel"]
    assert retrieved_measurement["weight"] == measurement_data["weight"]


def test_get_measurement_by_id_nonexisting():
    nonexistent_id = "nonexistent-id"  # Nahraďte nějakým neexistujícím ID
    response = requests.get(f"{BASE_URL}/measurements/{nonexistent_id}")
    assert response.status_code == 500  # Nebo jiný kód značící nenalezeno.