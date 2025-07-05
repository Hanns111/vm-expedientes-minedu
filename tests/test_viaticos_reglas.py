"""
Tests semánticos para verificar reglas específicas de viáticos
"""
import pytest
import requests
import json
import os

URL = "http://localhost:8001/api/chat/professional"
HEAD = {"Content-Type": "application/json"}

def ask(msg):
    """Helper para hacer consultas al endpoint profesional"""
    r = requests.post(URL, headers=HEAD, data=json.dumps({"message": msg}), timeout=60)
    r.raise_for_status()
    return r.text.lower()

def test_rendicion_10_dias():
    """Test para verificar que el sistema conoce el plazo de rendición de 10 días hábiles"""
    resp = ask("¿Cuántos días hábiles tengo para rendir los viáticos?")
    assert "10" in resp and "día" in resp, f"Respuesta no contiene plazo de 10 días: {resp}"

def test_deduccion_vehiculo():
    """Test para verificar que el sistema conoce la deducción del 30% por vehículo oficial"""
    resp = ask("¿Qué deducción se aplica si uso vehículo oficial del MINEDU?")
    assert "30" in resp and "%" in resp, f"Respuesta no contiene deducción del 30%: {resp}"

def test_numeral_8_4_2():
    """Test específico para el numeral 8.4.2"""
    resp = ask("¿Qué dice el numeral 8.4.2 sobre rendición de viáticos?")
    assert "8.4.2" in resp or "diez" in resp, f"Respuesta no menciona numeral 8.4.2: {resp}"

def test_numeral_7_6():
    """Test específico para el numeral 7.6"""
    resp = ask("¿Qué dice el numeral 7.6 sobre vehículo oficial?")
    assert "7.6" in resp or "vehículo oficial" in resp, f"Respuesta no menciona numeral 7.6: {resp}"

def test_sistema_funciona():
    """Test básico para verificar que el sistema responde"""
    resp = ask("¿Cuál es el monto de viáticos?")
    assert "s/" in resp or "soles" in resp, f"Sistema no responde correctamente: {resp}" 