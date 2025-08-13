# Bot de Trading para Bitunix con Telegram y TradingView

Este bot permite recibir señales de TradingView vía webhook, registrar operaciones, y cerrar operaciones automáticamente en Bitunix, notificando todo en Telegram.

## Características

- Recibe señales de TradingView por webhook.
- Envía notificaciones a Telegram con botones para registrar operaciones.
- Cierra operaciones automáticamente cuando llega la señal contraria.
- Calcula y muestra el PnL (ganancia/pérdida) al cerrar una operación.
- Fácil de desplegar en Render.com o cualquier VPS.

## Requisitos

- Python 3.8+
- Cuenta en Bitunix con claves API (solo permisos de trading y lectura)
- Bot de Telegram y tu chat ID
- Cuenta en Render.com (opcional, para despliegue rápido)

## Instalación

1. **Clona este repositorio:**

    ```bash
    git clone https://github.com/TU_USUARIO/bot-trading-bitunix.git
    cd bot-trading-bitunix
    ```

2. **Instala las dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configura las variables de entorno:**

    Puedes agregarlas en Render.com o en un archivo `.env`:

    ```
    TELEGRAM_TOKEN=tu_token_de_telegram
    CHAT_ID=tu_chat_id
    BITUNIX_API_KEY=tu_api_key_bitunix
    BITUNIX_API_SECRET=tu_api_secret_bitunix
    ```

4. **Ejecuta el bot localmente:**

    ```bash
    python bot.py
    ```

## Despliegue en Render.com

1. Sube tu código a un repositorio en GitHub.
2. Crea un nuevo Web Service en Render.com y conecta tu repo.
3. Añade las variables de entorno en la sección "Environment".
4. Render detectará `requirements.txt` y ejecutará `python bot.py`.
5. Usa la URL pública de Render para configurar el webhook en TradingView:

    ```
    https://TU_APP.onrender.com/webhook
    ```

## Uso

- Cuando TradingView envía una señal, el bot la notifica en Telegram con un botón para registrar la operación.
- Al registrar la operación, se guarda el ticker, tipo de señal y precio de entrada.
- Si llega una señal contraria, el bot cierra la operación automáticamente en Bitunix y muestra el resultado (PnL) en Telegram.

## Seguridad

- **No compartas tu API Secret.**
- No uses permisos de retiro en la API.
- Si usas un VPS con IP fija, vincula la IP en la configuración de la API de Bitunix.
- Si usas Render.com, deja el campo de IP vacío (menos seguro, pero necesario para pruebas rápidas).

## Créditos

Desarrollado por [Tu Nombre o Usuario].

---

