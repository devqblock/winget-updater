import os
import hashlib
import subprocess

# 1. Cleanly retrieve the version from the GitHub environment
# GitHub Actions automatically provides the GITHUB_REF_NAME variable (e.g., v1.1.3)
ref_name = os.environ.get("GITHUB_REF_NAME", "v0.0.0")
exe_name = f"WingetUpdater-{ref_name}"

print(f"--- Compiling {exe_name}.exe with PyInstaller ---")

# 2. We compile the executable with the correct version name.
cmd = [
    "pyinstaller", "--clean", "--noconfirm", "--onefile", "--windowed",
    "--name", exe_name, "--icon", "icono.ico",
    "--add-data", "icono.ico;.", "--manifest", "admin.manifest",
    "WingetUpdater.py"
]
subprocess.run(cmd, check=True)

# 3. Calculate the SHA256 hash of the generated executable.
exe_path = f"dist/{exe_name}.exe"
print(f"--- Calculating SHA256 Hash of {exe_path} ---")
hash_value = hashlib.sha256(open(exe_path, "rb").read()).hexdigest()

# 4. Create the checksums.txt file within the dist/ directory.
with open("dist/checksums.txt", "w") as f:
    f.write(f"{hash_value}  {exe_name}.exe\n")

print("--- Files ready. Creating Release on GitHub ---")

# 5. Generate the explanatory text in Markdown with the code blocks ready to copy and paste
body_text = f"""## 🚀 WingetUpdater {ref_name}
Automatically published new version!

### 🔒 Integrity Verification (SHA256)
The official SHA256 hash for this version is:
```text
{hash_value}
```

Open a terminal in your downloads folder and run the corresponding command to verify that the file is authentic:

#### 💻 PowerShell
```powershell
Get-FileHash .\\{exe_name}.exe -Algorithm SHA256
```
_(Compare that the result matches exactly with the official hash above)._

#### 📟 Command Prompt (CMD)
```cmd
certutil -hashfile {exe_name}.exe SHA256
```
_(Compare that the result matches exactly with the official hash above)._

---
_Generated automatically through GitHub Actions._"""

with open("dist/body.md", "w", encoding="utf-8") as f:
    f.write(body_text)

# 6. We use the official GitHub tool ('gh') that comes pre-installed on the servers
# to create the Release and upload the files without using third-party extensions
repo = os.environ.get("GITHUB_REPOSITORY")
release_cmd = [
    "gh", "release", "create", ref_name,
    f"dist/{exe_name}.exe",
    "dist/checksums.txt",
    "--target", "main",
    "--title", f"WingetUpdater {ref_name}",
    "--notes-file", "dist/body.md"
]

# We add the authentication token that the server provides to be able to publish
env_vars = os.environ.copy()
env_vars["GH_TOKEN"] = os.environ.get("GITHUB_TOKEN", "")

subprocess.run(release_cmd, env=env_vars, check=True)
print("--- Release successfully published to your repository! ---")
