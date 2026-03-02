import threading
import tkinter as tk
from tkinter import messagebox
import winsound
import traceback
from pathlib import Path

from plyer import notification


APP_NAME = "PosturApp"
DEFAULT_INTERVAL_SECONDS = 300


def _log_error(err: Exception) -> None:
    log_dir = Path.home() / "AppData" / "Local" / APP_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "posturapp.log"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"{type(err).__name__}: {err}\n")
        f.write(traceback.format_exc())
        f.write("\n---\n")


def enviar_notificacion() -> None:
    try:
        # More reliable than MessageBeep in packaged apps
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            winsound.Beep(1200, 250)

        notification.notify(
            title="🧘‍♂️ ¡POSTURA, FABRIZIO!",
            message="Hombros atrás y espalda recta. ¡No te encorves!",
            app_name=APP_NAME,
            timeout=10,
        )
    except Exception as e:
        _log_error(e)


def bucle_recordatorios(stop_event: threading.Event, interval_seconds: int) -> None:
    while not stop_event.is_set():
        enviar_notificacion()
        if stop_event.wait(interval_seconds):
            break


class PosturaApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.resizable(False, False)

        self.intervalo = DEFAULT_INTERVAL_SECONDS
        self.hilo_recordatorios: threading.Thread | None = None
        self.stop_event = threading.Event()

        self.estado_var = tk.StringVar(value="Detenido")
        self.intervalo_var = tk.StringVar(value=str(self.intervalo // 60))

        self._crear_ui()
        self._actualizar_estado()

        self.root.protocol("WM_DELETE_WINDOW", self._cerrar_app)

    def _crear_ui(self) -> None:
        frame = tk.Frame(self.root, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Recordatorio de postura", font=("Segoe UI", 12, "bold")).pack(anchor="w")

        estado_frame = tk.Frame(frame, pady=8)
        estado_frame.pack(fill="x")

        tk.Label(estado_frame, text="Estado:").pack(side="left")
        tk.Label(estado_frame, textvariable=self.estado_var, fg="blue").pack(side="left", padx=(6, 0))

        intervalo_frame = tk.Frame(frame, pady=8)
        intervalo_frame.pack(fill="x")

        tk.Label(intervalo_frame, text="Intervalo (min):").pack(side="left")
        tk.Entry(intervalo_frame, textvariable=self.intervalo_var, width=8).pack(side="left", padx=(8, 0))
        tk.Button(intervalo_frame, text="Aplicar", command=self._cambiar_intervalo).pack(side="left", padx=(8, 0))

        botones_frame = tk.Frame(frame, pady=8)
        botones_frame.pack(fill="x")

        tk.Button(botones_frame, text="Iniciar", width=12, command=self._iniciar_recordatorios).pack(side="left")
        tk.Button(botones_frame, text="Detener", width=12, command=self._detener_recordatorios).pack(side="left", padx=(8, 0))
        tk.Button(botones_frame, text="Probar", width=12, command=self._probar_notificacion).pack(side="left", padx=(8, 0))

    def _esta_activo(self) -> bool:
        return self.hilo_recordatorios is not None and self.hilo_recordatorios.is_alive()

    def _actualizar_estado(self) -> None:
        self.estado_var.set("Activo" if self._esta_activo() else "Detenido")

    def _iniciar_recordatorios(self) -> None:
        if self._esta_activo():
            messagebox.showinfo(APP_NAME, "Los recordatorios ya están activos.")
            return

        self.stop_event.clear()
        self.hilo_recordatorios = threading.Thread(
            target=bucle_recordatorios,
            args=(self.stop_event, self.intervalo),
            daemon=True,
        )
        self.hilo_recordatorios.start()
        self._actualizar_estado()

    def _detener_recordatorios(self) -> None:
        if not self._esta_activo():
            messagebox.showinfo(APP_NAME, "Los recordatorios ya están detenidos.")
            return

        self.stop_event.set()
        self.hilo_recordatorios.join(timeout=1)
        self._actualizar_estado()

    def _cambiar_intervalo(self) -> None:
        valor = self.intervalo_var.get().strip()
        if not valor.isdigit() or int(valor) <= 0:
            messagebox.showerror(APP_NAME, "Ingresa un número entero mayor a 0.")
            return

        self.intervalo = int(valor) * 60

        if self._esta_activo():
            self.stop_event.set()
            self.hilo_recordatorios.join(timeout=1)
            self.stop_event.clear()
            self.hilo_recordatorios = threading.Thread(
                target=bucle_recordatorios,
                args=(self.stop_event, self.intervalo),
                daemon=True,
            )
            self.hilo_recordatorios.start()

        messagebox.showinfo(APP_NAME, "Intervalo actualizado correctamente.")
        self._actualizar_estado()

    def _probar_notificacion(self) -> None:
        enviar_notificacion()

    def _cerrar_app(self) -> None:
        self.stop_event.set()
        if self._esta_activo():
            self.hilo_recordatorios.join(timeout=1)
        self.root.destroy()


def iniciar_app() -> None:
    root = tk.Tk()
    PosturaApp(root)
    root.mainloop()

    


if __name__ == "__main__":
    iniciar_app()