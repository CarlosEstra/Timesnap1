#!/usr/bin/env python3
"""
TimeSnap Server Launcher
Script para iniciar el servidor Flask de TimeSnap con configuración completa
para desarrollo local con soporte de cámara y multimedia.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Verificar que las dependencias necesarias estén instaladas"""
    try:
        import flask
        import flask_cors
        import mysql.connector
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Falta instalar dependencias: {e}")
        print("Ejecuta: pip install flask flask-cors mysql-connector-python")
        return False

def check_database_connection():
    """Verificar conexión a la base de datos"""
    try:
        from db_connection import get_db_connection
        mydb = get_db_connection()
        if mydb:
            mydb.close()
            print("✅ Conexión a base de datos exitosa")
            return True
        else:
            print("❌ Error de conexión a base de datos")
            return False
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        return False

def start_server():
    """Iniciar el servidor Flask"""
    print("🚀 Iniciando servidor TimeSnap...")
    print("=" * 50)
    print("📍 Servidor disponible en: http://127.0.0.1:5000/")
    print("📍 Servidor disponible en: http://localhost:5000/")
    print("=" * 50)
    print("🎥 Soporte completo para:")
    print("   • Acceso a cámara web")
    print("   • Reconocimiento facial")
    print("   • Multimedia y APIs modernas")
    print("=" * 50)
    print("💡 Para detener: Ctrl+C")
    print("=" * 50)

    try:
        # Ejecutar el servidor Flask
        os.system("python app.py")
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar servidor: {e}")

def main():
    """Función principal"""
    print("🎯 TimeSnap - Servidor de Desarrollo Local")
    print("=" * 50)

    # Verificar requisitos
    if not check_requirements():
        sys.exit(1)

    # Verificar base de datos
    if not check_database_connection():
        print("⚠️  Advertencia: No se pudo conectar a la base de datos")
        print("   El servidor se iniciará pero algunas funciones no estarán disponibles")

    # Iniciar servidor
    start_server()

if __name__ == "__main__":
    main()
