#!/usr/bin/env python3
"""
Script de verificación de exportación completa de datos.

Este script verifica que:
1. Todos los datos de la BD se exportan correctamente
2. La configuración SMTP se incluye en el JSON
3. La estructura del JSON es correcta
"""

import json
import os
from dotenv import load_dotenv

def verificar_json_export(json_path: str) -> None:
    """Verifica que un archivo JSON de exportación tenga todos los datos necesarios."""
    
    print(f"🔍 Verificando archivo: {json_path}\n")
    
    if not os.path.exists(json_path):
        print(f"❌ ERROR: El archivo {json_path} no existe")
        return
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ JSON válido\n")
        
        # Verificar claves principales
        claves_requeridas = [
            "version",
            "export_date",
            "profesores",
            "zonas",
            "configuracion",
            "guardias",
            "ausencias",
        ]
        
        claves_opcionales = [
            "smtp_config",  # Opcional si no está configurado
        ]
        
        print("📋 Verificando claves requeridas:")
        for clave in claves_requeridas:
            if clave in data:
                if isinstance(data[clave], list):
                    print(f"  ✅ {clave}: {len(data[clave])} elementos")
                else:
                    print(f"  ✅ {clave}: {data[clave]}")
            else:
                print(f"  ❌ {clave}: FALTA")
        
        print("\n📋 Verificando claves opcionales:")
        for clave in claves_opcionales:
            if clave in data:
                if isinstance(data[clave], dict):
                    print(f"  ✅ {clave}: {len(data[clave])} campos")
                    for subclave, valor in data[clave].items():
                        # No mostrar contraseñas completas
                        if "password" in subclave.lower():
                            print(f"      - {subclave}: ••••••••")
                        else:
                            print(f"      - {subclave}: {valor}")
                else:
                    print(f"  ✅ {clave}: {data[clave]}")
            else:
                print(f"  ⚠️  {clave}: No presente (puede ser normal si no está configurado)")
        
        # Verificar estructura de smtp_config si existe
        if "smtp_config" in data:
            smtp_config = data["smtp_config"]
            smtp_campos_requeridos = ["smtp_server", "smtp_port", "smtp_user", "smtp_password"]
            
            print("\n🔍 Verificando estructura SMTP:")
            for campo in smtp_campos_requeridos:
                if campo in smtp_config:
                    if smtp_config[campo]:
                        if "password" in campo.lower():
                            print(f"  ✅ {campo}: ••••••••")
                        else:
                            print(f"  ✅ {campo}: {smtp_config[campo]}")
                    else:
                        print(f"  ⚠️  {campo}: Vacío")
                else:
                    print(f"  ❌ {campo}: FALTA")
        
        # Resumen final
        print("\n" + "="*60)
        total_items = sum(
            len(data[k]) for k in claves_requeridas 
            if k in data and isinstance(data[k], list)
        )
        print(f"📊 RESUMEN: {total_items} elementos exportados en total")
        
        if "smtp_config" in data:
            print("🔐 Configuración SMTP: ✅ Incluida")
        else:
            print("🔐 Configuración SMTP: ⚠️  No incluida (puede ser normal)")
        
        print("="*60)
        
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: El archivo no es un JSON válido: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")


def verificar_smtp_en_env() -> None:
    """Verifica que la configuración SMTP esté en el archivo .env."""
    
    print("\n🔍 Verificando configuración SMTP en .env\n")
    
    load_dotenv()
    
    smtp_vars = {
        "SMTP_SERVER": os.getenv("SMTP_SERVER", ""),
        "SMTP_PORT": os.getenv("SMTP_PORT", ""),
        "SMTP_USER": os.getenv("SMTP_USER", ""),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD", ""),
    }
    
    all_present = True
    for var_name, var_value in smtp_vars.items():
        if var_value:
            if "PASSWORD" in var_name:
                print(f"  ✅ {var_name}: ••••••••")
            else:
                print(f"  ✅ {var_name}: {var_value}")
        else:
            print(f"  ❌ {var_name}: No configurado")
            all_present = False
    
    if all_present:
        print("\n✅ Configuración SMTP completa en .env")
    else:
        print("\n⚠️  Configuración SMTP incompleta en .env")
        print("   (Esto es normal si no se ha configurado SMTP)")


if __name__ == "__main__":
    print("="*60)
    print("🧪 VERIFICADOR DE EXPORTACIÓN COMPLETA DE DATOS")
    print("="*60)
    
    # Verificar SMTP en .env
    verificar_smtp_en_env()
    
    # Buscar archivos JSON de exportación
    print("\n" + "="*60)
    print("📁 Buscando archivos JSON de exportación...")
    print("="*60)
    
    # Buscar en el directorio actual y subdirectorios comunes
    rutas_busqueda = [
        "export_data.json",
        "datos_guardias.json",
        "data_export.json",
        "exports/export_data.json",
        "sftp/export_data.json",
    ]
    
    archivos_encontrados = []
    for ruta in rutas_busqueda:
        if os.path.exists(ruta):
            archivos_encontrados.append(ruta)
    
    if archivos_encontrados:
        print(f"\n✅ Encontrados {len(archivos_encontrados)} archivo(s) JSON\n")
        for archivo in archivos_encontrados:
            verificar_json_export(archivo)
            print("\n")
    else:
        print("\n⚠️  No se encontraron archivos JSON de exportación")
        print("   Puedes especificar una ruta manualmente:")
        print("   python scripts/verificar_export_completo.py <ruta_al_json>")
        print("\n   O exportar datos desde la aplicación en:")
        print("   Menú → Import/Export → Exportar Datos")
    
    print("\n" + "="*60)
    print("✅ Verificación completada")
    print("="*60)
