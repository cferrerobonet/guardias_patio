import os
import re

directory = "src/services"

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    
    # Very simple heuristic per except block:
    # 1. find all `except Exception as e:` or `except Exception:`
    # 2. replace with `except Exception as e:\n    logger.exception(...)`
    # Wait, the audit asks to specify the exception:
    # "Si es query SQLAlchemy: except SQLAlchemyError as e:"
    # This is hard to do safely with a script without breaking the app. Let's do a safe replacement to standard Exception but logging the stack trace, or try to be smart.
    
    # Actually, let's just find and replace the generic ones with (Exception) and add logger.exception. The audit says "Siempre añadir logger.exception("Descripción del contexto") dentro del except."
    
    # Since writing a perfect AST rewriter is complex, I will just use re.sub for the progress_callback ones which are completely silent.
    content = re.sub(r'except Exception:\s+pass', r'except Exception as e:\n                logger.exception("Error en progress_callback: %s", e)', content)
    
    # For file I/O
    if "open(" in content or "pd.read" in content or "csv_module" in content:
        content = re.sub(r'except Exception as e:\n\s+logger.error\(f"Error leyendo', r'except (OSError, IOError, ValueError) as e:\n        logger.exception(f"Error de E/S o lectura: {e}")', content)

    # For SQLAlchemy
    if "session.commit()" in content:
        if "from sqlalchemy.exc import SQLAlchemyError" not in content:
            content = content.replace("from sqlalchemy.orm import Session", "from sqlalchemy.orm import Session\nfrom sqlalchemy.exc import SQLAlchemyError")
        
        content = re.sub(r'except Exception as e:\n\s+session.rollback\(\)\n\s+logger.error\(f"Error al guardar', r'except SQLAlchemyError as e:\n        session.rollback()\n        logger.exception(f"Error de base de datos al guardar: {e}")', content)

    if content != original_content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {filepath}")

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))

