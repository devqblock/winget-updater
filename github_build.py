import os
import hashlib
import subprocess

# 1. Recuperamos la versión directamente desde el tag de GitHub Actions
version = os.environ.get("TAG_VERSION", "v0.0.0")
exe_name = f"WingetUpdater-{version}"

print(f"--- Compilando {exe_name}.exe con PyInstaller ---")

# 2. Ejecutamos el comando de PyInstaller de forma nativa
cmd = [
    "pyinstaller", "--clean", "--noconfirm", "--onefile", "--windowed",
    "--name", exe_name, "--icon", "icono.ico",
    "--add-data", "icono.ico;.", "--manifest", "admin.manifest",
    "WingetUpdater.py"
]
subprocess.run(cmd, check=True)

# 3. Calculamos el hash SHA256 del binario generado
exe_path = f"dist/{exe_name}.exe"
print(f"--- Generando Hash de {exe_path} ---")

hash_value = hashlib.sha256(open(exe_path, "rb").read()).hexdigest()

# 4. Creamos el archivo checksums.txt dentro de dist/
with open("dist/checksums.txt", "w") as f:
    f.write(f"{hash_value}  {exe_name}.exe\n")

# 5. Enviamos el hash a la memoria de GitHub Actions
with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"sha_hash={hash_value}\n")

print("--- Proceso de compilación completado con éxito ---")
