# Job Hunter Bot v4.0 - Instrucciones

## Novedades v4

- Menu con botones (ya no necesitas escribir comandos)
- Agrega cualquier sitio web para monitorear
- 11 portales fijos + tus sitios + canales Telegram

## Como funciona el menu

Envias /start y te aparecen botones:

- Buscar ahora: busca en todos los portales
- Keywords: ver, agregar o quitar palabras clave
- Excluidas: administrar exclusiones
- Canales TG: administrar canales de Telegram
- Sitios web: agregar cualquier URL para monitorear
- Config: ver resumen

Todo se maneja tocando botones, sin escribir comandos.

## Sitios web personalizados

Agrega cualquier pagina que publique ofertas, por ejemplo:

- https://www.empresa.com/careers
- https://www.computrabajo.com.ve/trabajo-de-redes
- https://www.indeed.com/jobs?q=soporte+remoto

El bot escanea la pagina buscando textos que coincidan con tus keywords.

## Instalacion en Railway

1. Bot en Telegram con @BotFather (2 min)
2. Subir 4 archivos a GitHub
3. railway.app, New Project, Deploy from GitHub
4. Variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, SEARCH_INTERVAL_MINUTES
5. Opcionales para canales: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE

## Para actualizar desde v3

Solo reemplaza main.py y requirements.txt en GitHub. Railway redespliegue solo.

## 11 portales fijos

LinkedIn, Computrabajo (VE/CO/AR/MX/PE/CL/EC), RemoteOK, Remotive, Jobicy, Arbeitnow, WeRemoto, RemoteJobs.lat, Empleate, Hireline, GetOnBoard
