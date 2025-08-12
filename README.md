# 📹 RTSP Camera Viewer - Backend

Backend del visor de cámara RTSP desarrollado en Python con Flask y WebSockets.

## 🚀 Características

- **Servidor Python**: Flask + Flask-SocketIO
- **Streaming RTSP**: Captura de video en tiempo real
- **WebSockets**: Comunicación bidireccional con el frontend
- **API REST**: Endpoints para control del stream
- **CORS habilitado**: Compatible con frontend en GitHub Pages

## 📋 Requisitos

- Python 3.8+
- OpenCV
- Flask
- Flask-SocketIO
- Numpy
- Pillow

## 🔧 Instalación Local

### 1. Clonar el repositorio
```bash
git clone <url-del-backend>
cd backend
```

### 2. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp env.example .env
# Editar .env con tu configuración RTSP
```

### 5. Ejecutar servidor
```bash
python server.py
```

## 🌐 Despliegue en Railway.app

### 1. Crear cuenta en Railway
- Ir a [railway.app](https://railway.app)
- Conectar con GitHub

### 2. Conectar repositorio
- Seleccionar este repositorio
- Railway detectará automáticamente Python

### 3. Configurar variables de entorno
En Railway Dashboard → Variables:
```
RTSP_URL=rtsp://admin:password@ip:port/stream
RTSP_USERNAME=admin
RTSP_PASSWORD=tu_password
RTSP_IP=tu_ip_camara
RTSP_PORT=555
```

### 4. Desplegar
- Railway construirá automáticamente
- URL disponible en el dashboard

## 🔌 API Endpoints

### GET `/`
- **Descripción**: Estado del servidor
- **Respuesta**: Información básica del API

### GET `/api/status`
- **Descripción**: Estado actual de la cámara
- **Respuesta**: Estado del stream y conexión

### POST `/api/stream/start`
- **Descripción**: Iniciar stream RTSP
- **Respuesta**: Confirmación de inicio

### POST `/api/stream/stop`
- **Descripción**: Detener stream RTSP
- **Respuesta**: Confirmación de parada

### GET `/api/test-rtsp`
- **Descripción**: Probar conexión RTSP
- **Respuesta**: Estado de la conexión

### GET `/api/test-connection`
- **Descripción**: Verificar OpenCV
- **Respuesta**: Versión y disponibilidad

### GET `/video_feed`
- **Descripción**: Stream MJPEG en tiempo real
- **Respuesta**: Video stream multipart

## 🔌 WebSocket Events

### Eventos del Cliente → Servidor
- `start_stream`: Iniciar stream
- `stop_stream`: Detener stream
- `ping`: Verificar conexión

### Eventos del Servidor → Cliente
- `status_update`: Actualización de estado
- `stream_started`: Stream iniciado
- `stream_stopped`: Stream detenido
- `video_frame`: Frame de video
- `pong`: Respuesta a ping

## 📁 Estructura del Proyecto

```
backend/
├── server.py          # Servidor principal
├── requirements.txt   # Dependencias Python
├── Procfile          # Configuración Railway
├── env.example       # Variables de entorno ejemplo
└── README.md         # Este archivo
```

## 🌍 Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `PORT` | Puerto del servidor | `5000` |
| `SECRET_KEY` | Clave secreta Flask | `rtsp-viewer-secret-key-2024` |
| `RTSP_URL` | URL completa RTSP | Configuración de ejemplo |
| `RTSP_USERNAME` | Usuario cámara | `admin` |
| `RTSP_PASSWORD` | Contraseña cámara | `Hik12345` |
| `RTSP_IP` | IP de la cámara | `181.115.147.116` |
| `RTSP_PORT` | Puerto RTSP | `555` |
| `RTSP_WIDTH` | Ancho de resolución | `1280` |
| `RTSP_HEIGHT` | Alto de resolución | `720` |
| `RTSP_FPS` | FPS del stream | `25` |

## 🔒 Seguridad

- **CORS habilitado** para desarrollo
- **Variables de entorno** para credenciales
- **Validación de entrada** en endpoints
- **Manejo de errores** robusto

## 🐛 Troubleshooting

### Error: "No module named 'cv2'"
```bash
pip install opencv-python
```

### Error: "Port already in use"
```bash
# Cambiar puerto en .env
PORT=5001
```

### Error: "RTSP connection failed"
- Verificar IP y puerto de la cámara
- Confirmar credenciales
- Verificar conectividad de red

## 📞 Soporte

Para problemas o preguntas:
1. Revisar logs del servidor
2. Verificar configuración RTSP
3. Comprobar conectividad de red
4. Abrir issue en el repositorio

## 📄 Licencia

Este proyecto está bajo licencia MIT.
