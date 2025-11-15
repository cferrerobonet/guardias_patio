# 🚀 Compilación Rápida - Guardias de Patio Windows

## Comando Único

```powershell
.\scripts\build_windows.ps1
```

## Requisitos Mínimos

- Python 3.13+
- Inno Setup 6.5.4+
- Venv en `C:\dev\guardias-patio\.venv`

## Verificación Antes de Compilar

```powershell
# ✅ Dependencias instaladas
C:\dev\guardias-patio\.venv\Scripts\pip.exe list | Select-String "matplotlib|reportlab|PyQt6"

# ❌ email_validator NO debe estar
C:\dev\guardias-patio\.venv\Scripts\pip.exe show email_validator
# Debe dar error "Package(s) not found"
```

## Problemas Comunes

| Error | Solución Rápida |
|-------|----------------|
| matplotlib faltante | `C:\dev\guardias-patio\.venv\Scripts\pip.exe install matplotlib>=3.7.0` |
| reportlab faltante | `C:\dev\guardias-patio\.venv\Scripts\pip.exe install reportlab>=4.0.0` |
| email_validator presente | `C:\dev\guardias-patio\.venv\Scripts\pip.exe uninstall -y email_validator` |
| Terminal colgado | **NO usar** `Start-Sleep` después de comandos largos |

## Resultado Esperado

```
✅ COMPILACIÓN COMPLETADA EXITOSAMENTE

Archivo: GuardiasDePatio-3.0.0-Windows-Setup.exe
Tamaño: ~69 MB
Ruta: C:\dev\gdp_out\
```

## Documentación Completa

- 📖 [Guía Completa](documentacion/BUILD_WINDOWS.md)
- ✅ [Checklist](.build-checklist.md)
- 🔧 [Script Automatizado](scripts/build_windows.ps1)

---

**Próxima compilación:** Solo ejecutar `.\scripts\build_windows.ps1` ✨
