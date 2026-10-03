import os
import hashlib
import subprocess

# 1. Obtenemos de forma limpia la versión desde el entorno de GitHub
# GitHub Actions nos da la variable GITHUB_REF_NAME automáticamente (ej: v1.1.3)
ref_name = os.environ.get("GITHUB_REF_NAME", "v0.0.0")
exe_name = f"WingetUpdater-{ref_name}"

print(f"--- Compilando {exe_name}.exe con PyInstaller ---")

# 2. Compilamos el ejecutable con el nombre correcto de la versión
cmd = [
    "pyinstaller", "--clean", "--noconfirm", "--onefile", "--windowed",
    "--name", exe_name, "--icon", "icono.ico",
    "--add-data", "icono.ico;.", "--manifest", "admin.manifest",
    "WingetUpdater.py"
]
subprocess.run(cmd, check=True)

# 3. Calculamos el hash SHA256 del ejecutable generado
exe_path = f"dist/{exe_name}.exe"
print(f"--- Generando Hash de {exe_path} ---")
hash_value = hashlib.sha256(open(exe_path, "rb").read()).hexdigest()

# 4. Creamos el archivo checksums.txt dentro de dist/
with open("dist/checksums.txt", "w") as f:
    f.write(f"{hash_value}  {exe_name}.exe\n")

print("--- Archivos listos. Creando Release en GitHub ---")

# 5. Generamos el texto explicativo en Markdown con los cuadros de código listos para copiar y pegar
body_text = f"""## 🚀 WingetUpdater {ref_name}
¡Nueva versión publicada automáticamente!

### 🔒 Verificación de Integridad (SHA256)
El hash SHA256 oficial para esta versión es:
```text
{hash_value}
```

Abre una terminal en tu carpeta de descargas y ejecuta el comando correspondiente para verificar que el archivo es auténtico:

#### 💻 PowerShell
```powershell
Get-FileHash .\\{exe_name}.exe -Algorithm SHA256
```
_(Compara que el resultado coincida exactamente con el hash oficial de arriba)._

#### 📟 Símbolo del sistema (CMD)
```cmd
certutil -hashfile {exe_name}.exe SHA256
```
_(Compara que el resultado coincida exactamente con el hash oficial de arriba)._

---
_Generado automáticamente mediante GitHub Actions._"""

with open("dist/body.md", "w", encoding="utf-8") as f:
    f.write(body_text)

# 6. Usamos la herramienta oficial de GitHub ('gh') que viene preinstalada en los servidores
# para crear el Release y subir los archivos sin usar extensiones de terceros
repo = os.environ.get("GITHUB_REPOSITORY")
release_cmd = [
    "gh", "release", "create", ref_name,
    f"dist/{exe_name}.exe",
    "dist/checksums.txt",
    "--target", "main",
    "--title", f"WingetUpdater {ref_name}",
    "--notes-file", "dist/body.md"
]

# Añadimos el token de autenticación que nos da el servidor para poder publicar
env_vars = os.environ.copy()
env_vars["GH_TOKEN"] = os.environ.get("GITHUB_TOKEN", "")

subprocess.run(release_cmd, env=env_vars, check=True)
print("--- ¡Release publicado con éxito en tu repositorio! ---")
