#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Backend para Visor de Cámara RTSP
Separado del frontend para deployment independiente
"""

import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, request, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import numpy as np
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la cámara desde variables de entorno
CAMERA_CONFIG = {
    'url': os.getenv('RTSP_URL', 'rtsp://admin:Hik12345@181.115.147.116:555/h264/ch1/main/av_stream'),
    'username': os.getenv('RTSP_USERNAME', 'admin'),
    'password': os.getenv('RTSP_PASSWORD', 'Hik12345'),
    'ip': os.getenv('RTSP_IP', '181.115.147.116'),
    'port': int(os.getenv('RTSP_PORT', '555')),
    'resolution': (int(os.getenv('RTSP_WIDTH', '1280')), int(os.getenv('RTSP_HEIGHT', '720'))),
    'fps': int(os.getenv('RTSP_FPS', '30')),  # Aumentar FPS por defecto
    'mjpeg_fps': int(os.getenv('MJPEG_FPS', '30'))  # FPS específico para MJPEG
}

# Variables globales del stream
stream_active = False
camera_thread = None
camera_cap = None
current_frame = None
stream_lock = threading.Lock()

# Configurar Flask con CORS
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'rtsp-viewer-secret-key-2024')
CORS(app, origins="*", supports_credentials=True)  # Permitir todas las origenes para desarrollo

# Configurar SocketIO para Render.com
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling']
)

def get_camera_status():
    """Obtener estado actual de la cámara"""
    return {
        'stream_active': stream_active,
        'camera_connected': camera_cap is not None and camera_cap.isOpened(),
        'url': CAMERA_CONFIG['url'],
        'ip': CAMERA_CONFIG['ip'],
        'port': CAMERA_CONFIG['port'],
        'timestamp': datetime.now().isoformat()
    }

def test_rtsp_connection():
    """Probar conexión RTSP con timeout"""
    try:
        print("🔍 Probando conexión RTSP...")
        
        # Crear captura temporal
        test_cap = cv2.VideoCapture(CAMERA_CONFIG['url'])
        
        if not test_cap.isOpened():
            return {
                'success': False,
                'error': 'No se pudo conectar a la cámara',
                'details': 'Verifica IP, puerto y credenciales'
            }
        
        # Intentar leer un frame
        ret, frame = test_cap.read()
        test_cap.release()
        
        if ret and frame is not None:
            return {
                'success': True,
                'message': 'Conexión RTSP exitosa',
                'details': f'Frame recibido: {frame.shape}',
                'resolution': f'{frame.shape[1]}x{frame.shape[0]}'
            }
        else:
            return {
                'success': False,
                'error': 'Conexión establecida pero no se reciben frames',
                'details': 'Verifica la ruta del stream RTSP'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Error al conectar: {str(e)}',
            'details': 'Verifica la configuración de la cámara'
        }

def camera_stream_thread():
    """Hilo principal para capturar video de la cámara"""
    global camera_cap, current_frame, stream_active
    
    try:
        print(f"📹 Conectando a cámara: {CAMERA_CONFIG['url']}")
        
        # Crear captura de video
        camera_cap = cv2.VideoCapture(CAMERA_CONFIG['url'])
        
        if not camera_cap.isOpened():
            print("❌ No se pudo abrir la cámara RTSP")
            stream_active = False
            return
        
        print("✅ Cámara RTSP conectada exitosamente")
        
        # Configurar propiedades para mejor rendimiento
        camera_cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_CONFIG['resolution'][0])
        camera_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_CONFIG['resolution'][1])
        camera_cap.set(cv2.CAP_PROP_FPS, CAMERA_CONFIG['fps'])
        
        # Optimizaciones para mejor rendimiento
        camera_cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo
        camera_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))  # Codec H.264
        
        frame_count = 0
        start_time = time.time()
        
        while stream_active and camera_cap.isOpened():
            ret, frame = camera_cap.read()
            
            if ret and frame is not None:
                with stream_lock:
                    current_frame = frame.copy()
                
                frame_count += 1
                
                # Calcular FPS cada segundo
                if frame_count % CAMERA_CONFIG['fps'] == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"📊 FPS: {fps:.1f}, Frames: {frame_count}, Delay: {frame_delay:.3f}s")
                    
                    # Ajustar FPS dinámicamente si es muy bajo
                    if fps < CAMERA_CONFIG['fps'] * 0.8:  # Si FPS es menor al 80% del esperado
                        frame_delay = max(0.01, frame_delay * 0.9)  # Reducir delay
                        print(f"⚡ Ajustando delay a: {frame_delay:.3f}s")
                
                # Enviar frame a clientes WebSocket
                try:
                    # Convertir frame a JPEG con calidad optimizada
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    if ret:
                        frame_data = buffer.tobytes()
                        socketio.emit('video_frame', {
                            'frame': frame_data.hex(),
                            'timestamp': datetime.now().isoformat(),
                            'frame_number': frame_count
                        })
                except Exception as e:
                    print(f"⚠️ Error enviando frame: {e}")
                
                # Control de FPS optimizado
                frame_delay = 1.0 / CAMERA_CONFIG['fps']
                time.sleep(frame_delay)
            else:
                print("⚠️ Frame no válido recibido")
                time.sleep(0.01)  # Reducir delay para frames inválidos
        
        print("📹 Hilo de cámara terminado")
        
    except Exception as e:
        print(f"❌ Error en hilo de cámara: {e}")
    finally:
        if camera_cap:
            camera_cap.release()
        stream_active = False

def start_camera_stream():
    """Iniciar stream de la cámara"""
    global stream_active, camera_thread
    
    if stream_active:
        print("⚠️ Stream ya está activo")
        return False
    
    try:
        stream_active = True
        camera_thread = threading.Thread(target=camera_stream_thread, daemon=True)
        camera_thread.start()
        
        print("🚀 Stream de cámara iniciado")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando stream: {e}")
        stream_active = False
        return False

def stop_camera_stream():
    """Detener stream de la cámara"""
    global stream_active, camera_thread, camera_cap
    
    try:
        stream_active = False
        
        if camera_cap:
            camera_cap.release()
            camera_cap = None
        
        if camera_thread and camera_thread.is_alive():
            camera_thread.join(timeout=2.0)
        
        print("⏹️ Stream de cámara detenido")
        return True
        
    except Exception as e:
        print(f"❌ Error deteniendo stream: {e}")
        return False

# Rutas de la API
@app.route('/')
def api_root():
    """Endpoint raíz de la API"""
    return jsonify({
        'message': 'RTSP Camera Viewer Backend API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/status')
def api_status():
    """Estado del sistema"""
    return jsonify(get_camera_status())

@app.route('/api/stream/start', methods=['POST'])
def api_start_stream():
    """Iniciar stream"""
    try:
        success = start_camera_stream()
        return jsonify({
            'success': success,
            'message': 'Stream iniciado' if success else 'Error al iniciar stream'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stream/stop', methods=['POST'])
def api_stop_stream():
    """Detener stream"""
    try:
        success = stop_camera_stream()
        return jsonify({
            'success': success,
            'message': 'Stream detenido' if success else 'Error al detener stream'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/test-rtsp')
def api_test_rtsp():
    """Probar conexión RTSP"""
    return jsonify(test_rtsp_connection())

@app.route('/api/test-connection')
def api_test_connection():
    """Probar si OpenCV está disponible"""
    try:
        # Verificar versión de OpenCV
        version = cv2.__version__
        return jsonify({
            'success': True,
            'message': 'OpenCV está disponible',
            'version': version
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OpenCV no está disponible',
            'details': str(e)
        })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    print(f"🔌 Cliente WebSocket conectado: {request.sid}")
    emit('status_update', get_camera_status())

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print(f"🔌 Cliente WebSocket desconectado: {request.sid}")

@socketio.on('start_stream')
def handle_start_stream():
    """Comando para iniciar stream"""
    success = start_camera_stream()
    emit('stream_started', {'success': success})

@socketio.on('stop_stream')
def handle_stop_stream():
    """Comando para detener stream"""
    success = stop_camera_stream()
    emit('stream_stopped', {'success': success})

@socketio.on('ping')
def handle_ping():
    """Ping del cliente"""
    emit('pong', {'timestamp': datetime.now().isoformat()})

# Función para generar stream MJPEG
def generate_mjpeg():
    """Generar stream MJPEG en tiempo real"""
    while stream_active:
        with stream_lock:
            if current_frame is not None:
                frame = current_frame.copy()
            else:
                # Frame de placeholder si no hay video
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, 'Sin Video', (200, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Convertir a JPEG con calidad optimizada para MJPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if ret:
            frame_data = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        
        # Optimizar delay para MJPEG
        time.sleep(0.033)  # ~30 FPS para MJPEG

@app.route('/video_feed')
def video_feed():
    """Endpoint para stream MJPEG"""
    return Response(generate_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("🚀 Iniciando Servidor Backend de Cámara RTSP")
    print(f"📹 Configuración de cámara: {CAMERA_CONFIG['url']}")
    print("🌐 Servidor disponible en: http://localhost:5000")
    print("📺 Stream MJPEG en: http://localhost:5000/video_feed")
    
    # Iniciar servidor
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
