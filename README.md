# 🐣 FocusOrDie

**Código de aplicación:** `VC002`  
**Versión:** 1.0.0  
**Plataformas:** Windows · macOS · Linux

---

## 📖 Descripción

**FocusOrDie** es una aplicación de escritorio tipo Pomodoro que gamifica la productividad con una **mascota virtual**. El temporizador alterna ciclos de **25 minutos de trabajo** y **5 minutos de descanso**, mientras la mascota reacciona a tus decisiones: pierde vida si pausas voluntariamente o si abres ventanas de distracción.

La interfaz es un **widget flotante** (siempre visible, modo oscuro con acentos neón) que muestra el tiempo restante, el estado emocional de la mascota, una barra de vida en tiempo real y alertas de audio según lo vaya el enfoque.

Si la mascota llega a **0 % de vida**, el temporizador se congela y aparece una pantalla dramática de *game over* para que vuelvas a centrarte.

---

## ✨ Características principales

| Función | Descripción |
|---------|-------------|
| ⏱️ **Temporizador Pomodoro** | Ciclos automáticos de 25 min trabajo / 5 min descanso con hilos en segundo plano |
| 🐣 **Mascota virtual** | Estados dinámicos (Trabajando, Finalizando, Descanso, Pausado, Procrastinando, Muerto, Éxito) |
| ❤️ **Sistema de vida** | Empieza al 100 %; penalización por pausa (−25 %) y drenaje continuo al procrastinar (−2 %/s) |
| 👁️ **Detector de ventanas** | Revisa cada 3 s la ventana activa y detecta distracciones (Twitter, X, YouTube, etc.) |
| 🔥 **Rachas** | +1 por cada Pomodoro completado; se reinicia al pausar o morir |
| 🎨 **Interfaz neón** | GUI con [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), modo oscuro y `always-on-top` |
| 🔊 **Alertas de audio** | Sonidos de éxito, derrota y aviso intermitente (winsound / afplay) |
| 💀 **Pantalla de muerte** | Modal dramático al agotar la vida de la mascota |
| ⚡ **Sin bloqueos** | Motor en hilos daemon; la GUI se refresca con `.after()` sin tirones |

---

## 🎯 Estados de la mascota

| Estado | Cuándo ocurre | Color en UI |
|--------|---------------|-------------|
| 🐣 **Trabajando** | Enfoque activo, más de 3 min restantes | Verde neón |
| 😰 **Finalizando** | Quedan menos de 3 minutos de trabajo | Verde neón |
| 😴 **Descanso** | Periodo de descanso de 5 minutos | Verde neón |
| 🎉 **Éxito** | Pomodoro de trabajo completado | Verde neón |
| 😑 **Pausado** | El usuario pausó manualmente (−25 % vida) | Rosa fosforito parpadeante |
| 😡 **Procrastinando** | Ventana prohibida abierta durante el trabajo | Rojo fuerte |
| ☠️ **Muerto** | La barra de vida llegó a 0 % | Rojo fuerte |

---

## 🚫 Ventanas prohibidas (detección automática)

El motor comprueba el **título de la ventana enfocada** cada 3 segundos. Si contiene alguna de estas palabras clave, activa el estado *Procrastinando* (salvo en pausa manual o descanso):

| Palabra clave | Ejemplos detectados |
|---------------|---------------------|
| Twitter | Pestañas y apps de Twitter |
| X | `x.com`, títulos tipo *Home / X* |
| YouTube | Navegador o app de YouTube |
| Facebook | Facebook en navegador o app |
| Instagram | Instagram web o escritorio |
| Netflix | Reproductor o web de Netflix |

> Durante el **descanso** no se aplica penalización por abrir estas ventanas.

---

## ❤️ Sistema de vida y rachas

| Evento | Efecto |
|--------|--------|
| Inicio de sesión | Vida al **100 %** |
| Pausa manual | **−25 %** de vida instantáneo; racha → 0 |
| Procrastinación | **−2 %** por cada segundo en ventana prohibida |
| Vida a 0 % | Estado **Muerto**; temporizador congelado; racha → 0 |
| Pomodoro completado | Racha **+1**; pitido de victoria |

**Barra de vida en la interfaz:**

| Vida restante | Color de la barra |
|---------------|-------------------|
| Más del 60 % | 🟢 Verde |
| Entre 30 % y 60 % | 🟡 Amarillo |
| Menos del 30 % | 🔴 Rojo |

---

## 🚀 Despliegue local (inicio rápido)

### Requisitos previos

- **Python 3.10+** ([descargar](https://www.python.org/downloads/))
- `pip` (incluido con Python)
- Tkinter (viene con la instalación estándar de Python en Windows y macOS)

### 1️⃣ Clonar o descargar el proyecto

```bash
git clone http://github.com/JBarraDev/VC002-FocusOrDie
cd VC002
```

O descomprime el ZIP del proyecto y abre una terminal en la carpeta `VC002`.

### 2️⃣ Crear entorno virtual (recomendado)

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4️⃣ Ejecutar la aplicación

```bash
python app.py
```

¡Listo! Se abrirá el widget flotante de **FocusOrDie** siempre visible sobre el resto de ventanas.

---

## 🖱️ Uso

1. Pulsa **Iniciar** para arrancar el temporizador y el detector de ventanas en segundo plano.
2. Trabaja durante el ciclo de **25 minutos**; el contador muestra el tiempo en formato `MM:SS`.
3. Si necesitas parar, pulsa **Pausar** (la mascota perderá un 25 % de vida y la racha se reiniciará).
4. Evita abrir redes sociales o streaming durante el trabajo: la mascota entrará en *Procrastinando* y perderá vida rápidamente.
5. Al completar un Pomodoro oírás un pitido de victoria y comenzará el **descanso de 5 minutos**.
6. Pulsa **Reiniciar** para restaurar ciclo, vida al 100 % y racha a 0.
7. Si la mascota muere, confirma el modal dramático y pulsa **Reiniciar y volver a intentarlo**.

---

## 🏗️ Estructura del proyecto

```
VC002/
├── app.py                       # Interfaz gráfica (punto de entrada)
├── engine.py                    # Motor lógico: temporizador, vida, estados, rachas
├── audio_alerts.py              # Alertas de audio (winsound / afplay)
├── requirements.txt             # Dependencias Python
├── README.md
├── LICENSE
└── doc/
    └── prompts.txt              # Especificaciones de desarrollo por fases
```

---

## 🧪 Probar el motor por consola

El archivo `engine.py` incluye un modo de prueba interactivo con ciclos acelerados (15 s trabajo / 8 s descanso):

```bash
python engine.py
```

Comandos en consola: `[p]` pausar · `[r]` reanudar · `[q]` salir.

---

## 🛠️ Stack tecnológico

- **Lenguaje:** Python 3
- **Interfaz:** CustomTkinter
- **Detección de ventanas:** pygetwindow
- **Audio:** `winsound` (Windows) · `afplay` (macOS) · terminal bell (fallback)
- **Concurrencia:** `threading` (motor) + `.after()` de Tkinter (GUI)
- **Arquitectura:** Motor lógico desacoplado + capa de presentación + módulo de audio

---

## 🔒 Comportamiento y privacidad

- ✅ Todo el procesamiento es **local**; no se envían datos a servidores externos
- ✅ Solo se lee el **título** de la ventana activa para detectar distracciones
- ✅ La detección de ventanas incluye control de excepciones ante errores del SO
- ❌ No se registran ni almacenan historiales de ventanas

---

## 🐛 Solución de problemas

| Problema | Solución |
|----------|----------|
| `ModuleNotFoundError: customtkinter` | Ejecuta `pip install -r requirements.txt` |
| La ventana no abre en Linux | Instala Tkinter: `sudo apt install python3-tk` (Debian/Ubuntu) |
| `python` no reconocido | Usa `python3` o reinstala Python marcando *Add to PATH* |
| No detecta ventanas prohibidas | Comprueba que `pygetwindow` esté instalado; en Linux la detección puede ser limitada |
| Sin sonido en Linux | El fallback usa el bell de la terminal; instala un servidor de sonido activo |

---

## 📄 Licencia

Proyecto de código abierto bajo licencia **MIT**. Consulta el archivo [`LICENSE`](LICENSE) en la raíz del repositorio.

---

## 🤝 Contribuciones

Las mejoras son bienvenidas: nuevas palabras clave de distracción, personalización de ciclos Pomodoro, skins de mascota, mejoras de UI o informes de errores. Abre un *issue* o envía un *pull request*.

---

## 📬 Información del proyecto

| Campo | Valor |
|-------|-------|
| **Nombre** | FocusOrDie |
| **Código** | VC002 |
| **Tipo** | Widget de productividad / Pomodoro gamificado |
| **Estado** | Fase 2 completada (motor + interfaz + audio) |

---

<p align="center">
  <strong>FocusOrDie · VC002</strong><br>
  <em>Céntrate, cuida a tu mascota, o muere intentándolo. 🐣⚡</em>
</p>
