# WingetUpdater.py
#
# Aplicacion de escritorio para gestionar actualizaciones con WinGet.
#
# Requisitos:
#   - Windows 10/11
#   - Python 3.10+
#   - WinGet instalado
#
# Ejecutar:
#   python WingetUpdater.py

import ctypes
import json
import locale
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk

APP_TITLE = "Qblock - WinGet Updater"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

TRANSLATIONS = {
    "Idioma": "Language",
    "Administrador": "Administrator",
    "Sin privilegios de administrador": "Not running as administrator",
    (
        "Comprueba las aplicaciones pendientes y utiliza recuperacion "
        "individual si una actualizacion no se completa."
    ): (
        "Check for pending updates and use individual recovery if an "
        "update does not complete."
    ),
    "Comprobar actualizaciones": "Check for updates",
    "Actualizar seleccionado": "Update selected",
    "Actualizar todo": "Update all",
    "Preparado": "Ready",
    "Programa": "Application",
    "Instalada": "Installed",
    "Disponible": "Available",
    "Origen": "Source",
    "Estado": "Status",
    "Registro": "Log",
    "Limpiar": "Clear",
    "Pendiente": "Pending",
    "Recuperando...": "Recovering...",
    "Actualizado": "Updated",
    "Actualizando...": "Updating...",
    "Comprobando actualizaciones...": "Checking for updates...",
    "No hay actualizaciones pendientes.": "No pending updates.",
    "1 actualizacion pendiente.": "1 pending update.",
    "{count} actualizaciones pendientes.": "{count} pending updates.",
    "Ejecutando actualizacion general...": "Running general update...",
    "\nLa actualizacion general termino correctamente.": (
        "\nThe general update completed successfully."
    ),
    "\nLa actualizacion general devolvio un error.": (
        "\nThe general update returned an error."
    ),
    "Comprobando paquetes que siguen pendientes...": (
        "Checking for packages that are still pending..."
    ),
    "\nNo quedan actualizaciones pendientes.": (
        "\nNo pending updates remain."
    ),
    "Todas las actualizaciones disponibles se han completado.": (
        "All available updates have been completed."
    ),
    "\nQuedan {count} paquete(s) pendiente(s).": (
        "\n{count} package(s) remain pending."
    ),
    "Se iniciara la recuperacion individual.": (
        "Starting individual recovery."
    ),
    "Recuperando {index}/{total}: {name}": (
        "Recovering {index}/{total}: {name}"
    ),
    "RECUPERACION INDIVIDUAL: {name}": "INDIVIDUAL RECOVERY: {name}",
    "ID: {package_id}": "ID: {package_id}",
    "OK: {name}": "OK: {name}",
    "ERROR: {name} (codigo {code})": "ERROR: {name} (code {code})",
    "Realizando comprobacion final...": "Performing final check...",
    "RESULTADO FINAL": "FINAL RESULT",
    "Sistema actualizado.": "System is up to date.",
    "Actualizacion completada": "Update completed",
    "No quedan aplicaciones pendientes de actualizar en WinGet.": (
        "There are no applications left to update in WinGet."
    ),
    "Siguen pendientes {count} paquete(s):": (
        "{count} package(s) are still pending:"
    ),
    " - {name} [{package_id}] {installed} -> {available}": (
        " - {name} [{package_id}] {installed} -> {available}"
    ),
    "Quedan {count} actualizaciones pendientes.": (
        "{count} updates remain pending."
    ),
    "Actualizaciones pendientes": "Pending updates",
    (
        "Quedan {count} paquete(s) que no se han podido actualizar.\n\n"
        "Consulta el registro inferior para ver los codigos de salida."
    ): (
        "{count} package(s) could not be updated.\n\n"
        "See the log below for the exit codes."
    ),
    "Selecciona primero una aplicacion.": "Select an application first.",
    "Actualizando {name}...": "Updating {name}...",
    "\n{name}: actualizacion completada.": "\n{name}: update completed.",
    "\n{name}: error {code}.": "\n{name}: error {code}.",
    "Comprobando resultado...": "Checking the result...",
    "{name} actualizado.": "{name} updated.",
    "{name} sigue pendiente.": "{name} is still pending.",
    "\nERROR INTERNO: {error_type}: {error}": (
        "\nINTERNAL ERROR: {error_type}: {error}"
    ),
    "Se ha producido un error:\n\n{error}": "An error occurred:\n\n{error}",
    "No se pudo interpretar la consulta como JSON. Usando salida de texto...": (
        "Could not parse the query as JSON. Using text output..."
    ),
    "[Codigo de salida: {code}]": "[Exit code: {code}]",
    "ERROR: winget.exe no se encuentra.": "ERROR: winget.exe was not found.",
    "ERROR ejecutando WinGet: {error}": "ERROR running WinGet: {error}",
    "Esta aplicacion esta disenada para Windows.": (
        "This application is designed for Windows."
    ),
    "No se pudieron obtener permisos de administrador.": (
        "Could not obtain administrator privileges."
    ),
    "Error solicitando permisos:\n{error}": (
        "Error requesting administrator privileges:\n{error}"
    ),
}


def detect_system_language():
    """Use the Windows display language, falling back to the process locale."""
    language = None

    if os.name == "nt":
        try:
            language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            language = locale.windows_locale.get(language_id)
        except (AttributeError, OSError):
            pass

    if not language:
        language = locale.getlocale()[0]

    return "es" if language and language.lower().startswith("es") else "en"


def translate_text(language, text, **values):
    translated = TRANSLATIONS.get(text, text) if language == "en" else text
    return translated.format(**values) if values else translated


@dataclass
class Package:
    name: str
    package_id: str
    installed_version: str
    available_version: str
    source: str = "winget"
    status: str = "Pendiente"

class WingetUpdater(tk.Tk):
    def __init__(self):
        super().__init__()

        self.language = detect_system_language()
        self.language_widgets = {}
        self.status_text = "Preparado"

         # Icono para ventana y barra de tareas
        import sys
        import os

        if getattr(sys, 'frozen', False):
             # Cuando está empaquetado con PyInstaller
            base_path = sys._MEIPASS
        else:
            # Cuando se ejecuta como script normal
            base_path = os.path.abspath(".")

        icon_path = os.path.join(base_path, "icono.ico")
        self.iconbitmap(icon_path)
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(950, 650)

        self.configure(bg="#0f172a")

        self.packages: dict[str, Package] = {}
        self.message_queue = queue.Queue()
        self.busy = False

        self._configure_styles()
        self._build_menu()
        self._build_ui()

        self.after(100, self._process_queue)
        self.after(400, self.refresh_updates)

    def _t(self, text, **values):
        return translate_text(self.language, text, **values)

    def _build_menu(self):
        self.menu = tk.Menu(self, tearoff=False)
        self.language_menu = tk.Menu(self.menu, tearoff=False)
        self.language_var = tk.StringVar(value=self.language)
        self.language_var.trace_add("write", self._on_language_selected)

        for language, label in (("es", "Español"), ("en", "English")):
            self.language_menu.add_radiobutton(
                label=label,
                variable=self.language_var,
                value=language,
            )

        self.menu.add_cascade(
            label=self._t("Idioma"),
            menu=self.language_menu,
        )
        self.configure(menu=self.menu)

    def _on_language_selected(self, *_):
        self.set_language(self.language_var.get())

    def set_language(self, language):
        if language not in ("es", "en"):
            raise ValueError(f"Unsupported language: {language}")

        if language == self.language:
            return

        self.language = language
        if self.language_var.get() != language:
            self.language_var.set(language)
        self.menu.entryconfigure(0, label=self._t("Idioma"))

        for widget, text in self.language_widgets.values():
            widget.configure(text=self._t(text))

        self.admin_label.configure(
            text=self._t(
                "Administrador"
                if self.is_admin()
                else "Sin privilegios de administrador"
            )
        )

        for column, text in (
            ("name", "Programa"),
            ("id", "ID"),
            ("installed", "Instalada"),
            ("available", "Disponible"),
            ("source", "Origen"),
            ("status", "Estado"),
        ):
            self.tree.heading(column, text=self._t(text))

        self.status_label.configure(text=self._t(self.status_text))

    # =========================================================
    # INTERFAZ
    # =========================================================

    def _configure_styles(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background="#111827",
            foreground="#e5e7eb",
            fieldbackground="#111827",
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Treeview.Heading",
            background="#1e293b",
            foreground="#f8fafc",
            relief="flat",
            font=("Segoe UI Semibold", 10),
            padding=(8, 10),
        )

        style.map(
            "Treeview",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")],
        )

        style.map(
            "Treeview.Heading",
            background=[("active", "#334155")],
        )

    def _build_ui(self):
        # Cabecera
        header = tk.Frame(self, bg="#0f172a")
        header.pack(fill="x", padx=28, pady=(24, 10))

        title = tk.Label(
            header,
            text="Qblock - WinGet Updater",
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI Semibold", 24),
        )
        title.pack(side="left")

        self.admin_label = tk.Label(
            header,
            text=self._t(
                "Administrador"
                if self.is_admin()
                else "Sin privilegios de administrador"
            ),
            bg="#0f172a",
            fg="#22c55e" if self.is_admin() else "#f59e0b",
            font=("Segoe UI", 10),
        )
        self.admin_label.pack(side="right", pady=8)

        subtitle = tk.Label(
            self,
            text=self._t(
                "Comprueba las aplicaciones pendientes y utiliza recuperacion "
                "individual si una actualizacion no se completa."
            ),
            bg="#0f172a",
            fg="#94a3b8",
            font=("Segoe UI", 10),
            anchor="w",
        )
        subtitle.pack(fill="x", padx=30, pady=(0, 18))

        self.language_widgets["subtitle"] = (
            subtitle,
            "Comprueba las aplicaciones pendientes y utiliza recuperacion "
            "individual si una actualizacion no se completa.",
        )

        # Barra de acciones
        toolbar = tk.Frame(self, bg="#0f172a")
        toolbar.pack(fill="x", padx=28, pady=(0, 14))

        self.refresh_button = self._button(
            toolbar,
            self._t("Comprobar actualizaciones"),
            self.refresh_updates,
            "#334155",
        )
        self.refresh_button.pack(side="left")

        self.update_selected_button = self._button(
            toolbar,
            self._t("Actualizar seleccionado"),
            self.update_selected,
            "#475569",
        )
        self.update_selected_button.pack(side="left", padx=(10, 0))

        self.update_all_button = self._button(
            toolbar,
            self._t("Actualizar todo"),
            self.update_all,
            "#2563eb",
        )
        self.update_all_button.pack(side="right")

        # Estado global
        status_frame = tk.Frame(self, bg="#1e293b")
        status_frame.pack(fill="x", padx=28, pady=(0, 14))

        self.status_label = tk.Label(
            status_frame,
            text=self._t(self.status_text),
            bg="#1e293b",
            fg="#e2e8f0",
            font=("Segoe UI Semibold", 10),
            anchor="w",
            padx=15,
            pady=11,
        )
        self.status_label.pack(fill="x")

        # Tabla
        tree_container = tk.Frame(self, bg="#111827")
        tree_container.pack(fill="both", expand=True, padx=28)

        columns = (
            "name",
            "id",
            "installed",
            "available",
            "source",
            "status",
        )

        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("name", text=self._t("Programa"))
        self.tree.heading("id", text=self._t("ID"))
        self.tree.heading("installed", text=self._t("Instalada"))
        self.tree.heading("available", text=self._t("Disponible"))
        self.tree.heading("source", text=self._t("Origen"))
        self.tree.heading("status", text=self._t("Estado"))

        self.tree.column("name", width=260, minwidth=160)
        self.tree.column("id", width=280, minwidth=180)
        self.tree.column("installed", width=105, anchor="center")
        self.tree.column("available", width=105, anchor="center")
        self.tree.column("source", width=80, anchor="center")
        self.tree.column("status", width=130, anchor="center")

        scrollbar = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self.tree.yview,
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Consola
        console_header = tk.Frame(self, bg="#0f172a")
        console_header.pack(fill="x", padx=28, pady=(18, 5))

        log_label = tk.Label(
            console_header,
            text=self._t("Registro"),
            bg="#0f172a",
            fg="#cbd5e1",
            font=("Segoe UI Semibold", 10),
        )
        log_label.pack(side="left")

        clear_button = self._button(
            console_header,
            self._t("Limpiar"),
            self.clear_log,
            "#334155",
            small=True,
        )
        clear_button.pack(side="right")

        self.language_widgets.update({
            "refresh": (self.refresh_button, "Comprobar actualizaciones"),
            "update_selected": (
                self.update_selected_button,
                "Actualizar seleccionado",
            ),
            "update_all": (self.update_all_button, "Actualizar todo"),
            "clear_log": (clear_button, "Limpiar"),
        })
        self.language_widgets["log"] = (log_label, "Registro")
        self.language_widgets["status"] = (
            self.status_label,
            "Preparado",
        )

        self.console = tk.Text(
            self,
            height=10,
            bg="#020617",
            fg="#cbd5e1",
            insertbackground="white",
            relief="flat",
            padx=14,
            pady=12,
            font=("Consolas", 9),
            wrap="word",
        )
        self.console.pack(fill="x", padx=28, pady=(0, 24))

    def _button(self, parent, text, command, color, small=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg="#ffffff",
            activebackground="#3b82f6",
            activeforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            padx=14 if small else 18,
            pady=6 if small else 9,
            font=("Segoe UI Semibold", 9 if small else 10),
        )

    # =========================================================
    # ADMINISTRADOR
    # =========================================================

    @staticmethod
    def is_admin():
        if os.name != "nt":
            return True

        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def restart_as_admin():
        params = subprocess.list2cmdline(sys.argv)

        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            params,
            None,
            1,
        )

    # =========================================================
    # EJECUCION DE WINGET
    # =========================================================

    def run_command(self, args, stream=True):
        command = ["winget"] + args

        self.log(
            "\n> " + subprocess.list2cmdline(command) + "\n"
        )

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=CREATE_NO_WINDOW,
            )

            output_lines = []

            if process.stdout:
                for line in process.stdout:
                    output_lines.append(line)

                    if stream:
                        self.log(line.rstrip())

            return_code = process.wait()
            output = "".join(output_lines)

            self.log(
                self._t("[Codigo de salida: {code}]", code=return_code)
            )

            return return_code, output

        except FileNotFoundError:
            self.log("ERROR: winget.exe no se encuentra.")
            return 9009, ""

        except Exception as exc:
            self.log(
                self._t("ERROR ejecutando WinGet: {error}", error=exc)
            )
            return -1, ""

    # =========================================================
    # JSON DE WINGET
    # =========================================================

    def get_upgrade_packages(self, include_unknown=True, include_pinned=False):
        """
        Intenta obtener las actualizaciones usando salida JSON.

        Si la version concreta de WinGet no acepta --output json para
        upgrade, usa el parser de texto como fallback.
        """

        args = ["upgrade"]

        if include_unknown:
            args.append("--include-unknown")

        if include_pinned:
            args.append("--include-pinned")

        args += [
            "--accept-source-agreements",
            "--disable-interactivity",
            "--output",
            "json",
        ]

        code, output = self.run_command(args, stream=False)

        if code == 0:
            packages = self.parse_json_packages(output)

            if packages is not None:
                return packages

        # Fallback
        self.log(
            "No se pudo interpretar la consulta como JSON. "
            "Usando salida de texto..."
        )

        return self.get_upgrade_packages_text(
            include_unknown=include_unknown,
            include_pinned=include_pinned,
        )

    def parse_json_packages(self, output):
        try:
            start = output.find("{")
            start_array = output.find("[")

            if start == -1 and start_array == -1:
                return []

            if start_array != -1 and (start == -1 or start_array < start):
                data = json.loads(output[start_array:])
            else:
                data = json.loads(output[start:])

            found = []

            def walk(obj):
                if isinstance(obj, dict):
                    package_id = (
                        obj.get("PackageIdentifier")
                        or obj.get("Id")
                        or obj.get("PackageId")
                    )

                    name = (
                        obj.get("PackageName")
                        or obj.get("Name")
                    )

                    available = (
                        obj.get("AvailableVersion")
                        or obj.get("Available")
                    )

                    installed = (
                        obj.get("InstalledVersion")
                        or obj.get("Version")
                    )

                    source = (
                        obj.get("SourceIdentifier")
                        or obj.get("Source")
                        or "winget"
                    )

                    if package_id and name and available:
                        found.append(
                            Package(
                                name=str(name),
                                package_id=str(package_id),
                                installed_version=str(installed or "Unknown"),
                                available_version=str(available),
                                source=str(source),
                            )
                        )

                    for value in obj.values():
                        walk(value)

                elif isinstance(obj, list):
                    for item in obj:
                        walk(item)

            walk(data)

            # Eliminar duplicados por ID
            unique = {}

            for package in found:
                unique[package.package_id] = package

            return list(unique.values())

        except Exception:
            return None

    # =========================================================
    # PARSER DE TEXTO
    # =========================================================

    def get_upgrade_packages_text(
        self,
        include_unknown=True,
        include_pinned=False,
    ):
        args = ["upgrade"]

        if include_unknown:
            args.append("--include-unknown")

        if include_pinned:
            args.append("--include-pinned")

        args += [
            "--accept-source-agreements",
            "--disable-interactivity",
        ]

        code, output = self.run_command(args, stream=False)

        return self.parse_upgrade_table(output)

    @staticmethod
    def parse_upgrade_table(output):
        """
        Parser para la tabla textual de WinGet.

        Busca la linea de separadores:
        --------------------------------------------------------
        y procesa las lineas posteriores.
        """

        lines = output.splitlines()

        separator_index = None

        for index, line in enumerate(lines):
            stripped = line.strip()

            if stripped and set(stripped) == {"-"}:
                separator_index = index
                break

        if separator_index is None:
            return []

        packages = []

        for line in lines[separator_index + 1:]:
            line = line.rstrip()

            if not line:
                continue

            lower = line.lower()

            if (
                "actualizaciones disponibles" in lower
                or "actualización disponible" in lower
                or "actualizaciones disponible" in lower
                or "paquete(s)" in lower
                or "paquetes tienen" in lower
                or "package(s)" in lower
                or "upgrades available" in lower
            ):
                continue

            # WinGet separa las columnas mediante varios espacios.
            import re

            parts = re.split(r"\s{2,}", line.strip())

            if len(parts) < 4:
                continue

            source = "winget"

            if len(parts) >= 5:
                source = parts[-1]
                available = parts[-2]
                installed = parts[-3]
                package_id = parts[-4]
                name = " ".join(parts[:-4])

            else:
                available = parts[-1]
                installed = parts[-2]
                package_id = parts[-3]
                name = " ".join(parts[:-3])

            if not name or not package_id:
                continue

            packages.append(
                Package(
                    name=name,
                    package_id=package_id,
                    installed_version=installed,
                    available_version=available,
                    source=source,
                )
            )

        return packages

    # =========================================================
    # ACTUALIZACIONES
    # =========================================================

    def refresh_updates(self):
        if self.busy:
            return

        self._start_worker(self._refresh_worker)

    def _refresh_worker(self):
        self.set_status("Comprobando actualizaciones...")

        packages = self.get_upgrade_packages(
            include_unknown=True,
            include_pinned=False,
        )

        self.packages = {
            package.package_id: package
            for package in packages
        }

        self.message_queue.put(("refresh_tree", None))

        count = len(packages)

        if count == 0:
            self.set_status("No hay actualizaciones pendientes.")
        elif count == 1:
            self.set_status("1 actualizacion pendiente.")
        else:
            self.set_status(
                self._t("{count} actualizaciones pendientes.", count=count)
            )

    def update_all(self):
        if self.busy:
            return

        self._start_worker(self._update_all_worker)

    def _update_all_worker(self):
        self.set_status("Ejecutando actualizacion general...")

        # -----------------------------------------------------
        # PASO 1
        # Intento normal de WinGet
        # -----------------------------------------------------

        global_args = [
            "upgrade",
            "--all",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]

        global_code, _ = self.run_command(global_args)

        if global_code == 0:
            self.log(
                "\nLa actualizacion general termino correctamente."
            )
        else:
            self.log(
                "\nLa actualizacion general devolvio un error."
            )

        # -----------------------------------------------------
        # PASO 2
        # IMPORTANTE:
        # No confiamos exclusivamente en el codigo de salida.
        #
        # Volvemos a comprobar TODOS los paquetes pendientes,
        # incluidos los de version Unknown.
        # -----------------------------------------------------

        self.set_status(
            "Comprobando paquetes que siguen pendientes..."
        )

        remaining = self.get_upgrade_packages(
            include_unknown=True,
            include_pinned=False,
        )

        if not remaining:
            self.log(
                "\nNo quedan actualizaciones pendientes."
            )
            self.set_status(
                "Todas las actualizaciones disponibles se han completado."
            )

            self.packages = {}
            self.message_queue.put(("refresh_tree", None))
            return

        # Actualizamos la tabla antes de recuperar
        self.packages = {
            package.package_id: package
            for package in remaining
        }

        self.message_queue.put(("refresh_tree", None))

        self.log(
            self._t(
                "\nQuedan {count} paquete(s) pendiente(s).",
                count=len(remaining),
            )
        )

        self.log(
            "Se iniciara la recuperacion individual."
        )

        # -----------------------------------------------------
        # PASO 3
        # Reintento individual GENERICO.
        #
        # NO existe ninguna excepcion especifica para SQL Server.
        #
        # Cada paquete pendiente utiliza SU PROPIO ID:
        #
        # winget upgrade
        #   --id ID
        #   --exact
        #   --include-unknown
        #   --interactive
        # -----------------------------------------------------

        failed_packages = []

        for index, package in enumerate(remaining, start=1):
            self.set_status(
                self._t(
                    "Recuperando {index}/{total}: {name}",
                    index=index,
                    total=len(remaining),
                    name=package.name,
                )
            )

            self.update_package_status(
                package.package_id,
                "Recuperando...",
            )

            self.log("")
            self.log("=" * 70)
            self.log(
                self._t("RECUPERACION INDIVIDUAL: {name}", name=package.name)
            )
            self.log(self._t("ID: {package_id}", package_id=package.package_id))
            self.log("=" * 70)

            recovery_args = [
                "upgrade",
                "--id",
                package.package_id,
                "--exact",
                "--include-unknown",
                "--interactive",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ]

            recovery_code, _ = self.run_command(
                recovery_args,
                stream=True,
            )

            if recovery_code == 0:
                self.update_package_status(
                    package.package_id,
                    "Actualizado",
                )

                self.log(self._t("OK: {name}", name=package.name))

            else:
                package.status = (
                    f"Error ({recovery_code})"
                )

                failed_packages.append(
                    (package, recovery_code)
                )

                self.update_package_status(
                    package.package_id,
                    package.status,
                )

                self.log(
                    self._t(
                        "ERROR: {name} (codigo {code})",
                        name=package.name,
                        code=recovery_code,
                    )
                )

        # -----------------------------------------------------
        # PASO 4
        # Verificacion final
        # -----------------------------------------------------

        self.set_status("Realizando comprobacion final...")

        final_remaining = self.get_upgrade_packages(
            include_unknown=True,
            include_pinned=False,
        )

        self.packages = {
            package.package_id: package
            for package in final_remaining
        }

        self.message_queue.put(("refresh_tree", None))

        self.log("")
        self.log("=" * 70)
        self.log("RESULTADO FINAL")
        self.log("=" * 70)

        if not final_remaining:
            self.log(
                "Todas las actualizaciones disponibles "
                "se han completado."
            )

            self.set_status(
                "Sistema actualizado."
            )

            self.message_queue.put(
                (
                    "info",
                    (
                        "Actualizacion completada",
                        "No quedan aplicaciones pendientes "
                        "de actualizar en WinGet.",
                    ),
                )
            )

        else:
            self.log(
                self._t(
                    "Siguen pendientes {count} paquete(s):",
                    count=len(final_remaining),
                )
            )

            for package in final_remaining:
                self.log(
                    self._t(
                        " - {name} [{package_id}] {installed} -> {available}",
                        name=package.name,
                        package_id=package.package_id,
                        installed=package.installed_version,
                        available=package.available_version,
                    )
                )

            self.set_status(
                self._t(
                    "Quedan {count} actualizaciones pendientes.",
                    count=len(final_remaining),
                )
            )

            self.message_queue.put(
                (
                    "warning",
                    (
                        "Actualizaciones pendientes",
                        self._t(
                            "Quedan {count} paquete(s) que no se han podido "
                            "actualizar.\n\nConsulta el registro inferior "
                            "para ver los codigos de salida.",
                            count=len(final_remaining),
                        ),
                    ),
                )
            )

    # =========================================================
    # ACTUALIZACION INDIVIDUAL
    # =========================================================

    def update_selected(self):
        if self.busy:
            return

        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                self._t(APP_TITLE),
                self._t("Selecciona primero una aplicacion."),
            )
            return

        item = self.tree.item(selected[0])

        values = item.get("values", [])

        if len(values) < 2:
            return

        package_id = values[1]

        package = self.packages.get(package_id)

        if not package:
            return

        self._start_worker(
            lambda: self._update_single_worker(package)
        )

    def _update_single_worker(self, package):
        self.set_status(
            self._t("Actualizando {name}...", name=package.name)
        )

        self.update_package_status(
            package.package_id,
            "Actualizando...",
        )

        args = [
            "upgrade",
            "--id",
            package.package_id,
            "--exact",
            "--include-unknown",
            "--interactive",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]

        code, _ = self.run_command(args)

        if code == 0:
            self.log(
                self._t(
                    "\n{name}: actualizacion completada.",
                    name=package.name,
                )
            )
        else:
            self.log(
                self._t(
                    "\n{name}: error {code}.",
                    name=package.name,
                    code=code,
                )
            )

        self.set_status("Comprobando resultado...")

        packages = self.get_upgrade_packages(
            include_unknown=True,
            include_pinned=False,
        )

        self.packages = {
            item.package_id: item
            for item in packages
        }

        self.message_queue.put(("refresh_tree", None))

        if package.package_id not in self.packages:
            self.set_status(
                self._t("{name} actualizado.", name=package.name)
            )
        else:
            self.set_status(
                self._t("{name} sigue pendiente.", name=package.name)
            )

    # =========================================================
    # THREADS
    # =========================================================

    def _start_worker(self, function):
        if self.busy:
            return

        self.busy = True
        self.message_queue.put(("buttons", False))

        def runner():
            try:
                function()

            except Exception as exc:
                self.log(
                    self._t(
                        "\nERROR INTERNO: {error_type}: {error}",
                        error_type=type(exc).__name__,
                        error=exc,
                    )
                )

                self.message_queue.put(
                    (
                        "error",
                        (
                            APP_TITLE,
                            self._t(
                                "Se ha producido un error:\n\n{error}",
                                error=exc,
                            ),
                        ),
                    )
                )

            finally:
                self.busy = False
                self.message_queue.put(("buttons", True))

        thread = threading.Thread(
            target=runner,
            daemon=True,
        )

        thread.start()

    # =========================================================
    # COLA UI
    # =========================================================

    def log(self, text):
        self.message_queue.put(("log", str(text)))

    def set_status(self, text):
        self.message_queue.put(("status", text))

    def update_package_status(self, package_id, status):
        self.message_queue.put(
            (
                "package_status",
                (package_id, status),
            )
        )

    def _process_queue(self):
        try:
            while True:
                message_type, payload = self.message_queue.get_nowait()

                if message_type == "log":
                    self.console.insert(
                        "end",
                        self._t(payload) + "\n",
                    )

                    self.console.see("end")

                elif message_type == "status":
                    self.status_text = payload
                    self.status_label.config(
                        text=self._t(payload),
                    )

                elif message_type == "refresh_tree":
                    self._refresh_tree_ui()

                elif message_type == "package_status":
                    package_id, status = payload

                    if package_id in self.packages:
                        self.packages[
                            package_id
                        ].status = status

                    self._refresh_tree_ui()

                elif message_type == "buttons":
                    state = (
                        tk.NORMAL
                        if payload
                        else tk.DISABLED
                    )

                    self.refresh_button.config(state=state)
                    self.update_all_button.config(state=state)
                    self.update_selected_button.config(
                        state=state
                    )

                elif message_type == "info":
                    title, message = payload
                    messagebox.showinfo(
                        self._t(title),
                        self._t(message),
                    )

                elif message_type == "warning":
                    title, message = payload
                    messagebox.showwarning(
                        self._t(title),
                        self._t(message),
                    )

                elif message_type == "error":
                    title, message = payload
                    messagebox.showerror(
                        self._t(title),
                        self._t(message),
                    )

        except queue.Empty:
            pass

        self.after(100, self._process_queue)

    def _refresh_tree_ui(self):
        selected_id = None

        selected = self.tree.selection()

        if selected:
            values = self.tree.item(
                selected[0]
            ).get("values", [])

            if len(values) >= 2:
                selected_id = values[1]

        for item in self.tree.get_children():
            self.tree.delete(item)

        selected_item = None

        packages = sorted(
            self.packages.values(),
            key=lambda p: p.name.lower(),
        )

        for package in packages:
            iid = self.tree.insert(
                "",
                "end",
                values=(
                    package.name,
                    package.package_id,
                    package.installed_version,
                    package.available_version,
                    package.source,
                    self._t(package.status),
                ),
            )

            if package.package_id == selected_id:
                selected_item = iid

        if selected_item:
            self.tree.selection_set(selected_item)
            self.tree.focus(selected_item)

    def clear_log(self):
        self.console.delete("1.0", "end")


# =============================================================
# MAIN
# =============================================================

def main():
    language = detect_system_language()

    # Comprobar WinGet antes de elevar.
    if os.name != "nt":
        messagebox.showerror(
            APP_TITLE,
            translate_text(
                language,
                "Esta aplicacion esta disenada para Windows.",
            ),
        )
        return

    # Ejecutar siempre como administrador.
    try:
        is_admin = (
            ctypes.windll.shell32.IsUserAnAdmin() != 0
        )
    except Exception:
        is_admin = False

    if not is_admin:
        try:
            params = subprocess.list2cmdline(sys.argv)

            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                params,
                None,
                1,
            )

            if result <= 32:
                ctypes.windll.user32.MessageBoxW(
                    None,
                    translate_text(
                        language,
                        "No se pudieron obtener permisos de administrador.",
                    ),
                    APP_TITLE,
                    0x10,
                )

        except Exception as exc:
            ctypes.windll.user32.MessageBoxW(
                None,
                translate_text(
                    language,
                    "Error solicitando permisos:\n{error}",
                    error=exc,
                ),
                APP_TITLE,
                0x10,
            )

        return

    app = WingetUpdater()
    app.mainloop()


if __name__ == "__main__":
    main()