import re

file_path = "docs/AUDITORIA_INTEGRAL_2026.md"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

def cross_out(issue_id, text_pattern):
    global content
    content = re.sub(
        rf"(\|\s*\d+\s*\|\s*{issue_id}\s*\|\s*)({text_pattern})(\s*\|\s*[SMLXL]+\s*\|)",
        r"\1~~\2~~ ✅ RESUELTO v5.1.0\3",
        content
    )

cross_out("ARQ-09", r"[^\|]+")
cross_out("SEC-17", r"[^\|]+")
cross_out("RES-05", r"[^\|]+")
cross_out("ARQ-08", r"[^\|]+")
cross_out("VIS-01", r"[^\|]+")
cross_out("VIS-02", r"[^\|]+")
cross_out("VIS-03", r"[^\|]+")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated docs/AUDITORIA_INTEGRAL_2026.md")
