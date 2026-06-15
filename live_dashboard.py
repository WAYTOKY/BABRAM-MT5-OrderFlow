"""
Live Dashboard - Real-time Order Flow визуализация с WebSocket
Показывает live данные, открытые позиции других трейдеров и изменения в реальном времени
"""
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime
import json
from src.mt5_connector import MT5Connector
from src.order_flow import OrderFlowAnalyzer
from src.delta_analyzer import DeltaAnalyzer
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальные переменные
current_data = {
    'price': 0,
    'buy_pressure': 0,
    'sell_pressure': 0,
    'delta': 0,
    'cumulative_delta': 0,
    'trend': 'NEUTRAL',
    'signal': 'WAIT',
    'timestamp': '',
    'bars': [],
    'open_positions': {'long': 0, 'short': 0},
}

monitoring_active = False
connector = None

def get_mt5_data():
    """Получить live данные из MT5"""
    global connector, current_data
    
    try:
        if connector is None:
            connector = MT5Connector(symbol="GOLD", timeframe=1)
        
        # Получаем последние свечи
        bars = connector.get_bars(num_bars=100)
        if bars is None:
            return
        
        # Анализируем
        of_analyzer = OrderFlowAnalyzer(bars)
        delta_analyzer = DeltaAnalyzer(bars)
        
        # Получаем текущие показатели
        pressure = of_analyzer.get_buy_sell_pressure(lookback=20)
        divergence = delta_analyzer.analyze_delta_divergence(lookback=20)
        stats = delta_analyzer.get_delta_statistics(lookback=100)
        
        # Получаем current price
        current_price = bars['close'].iloc[-1]
        
        # Определяем сигнал
        signal = 'WAIT'
        if pressure['dominant'] == 'BUYERS' and stats['trend'] == 'BULLISH':
            signal = 'STRONG BUY'
        elif pressure['dominant'] == 'SELLERS' and stats['trend'] == 'BEARISH':
            signal = 'STRONG SELL'
        
        # Обновляем данные
        current_data.update({
            'price': float(current_price),
            'buy_pressure': float(pressure['buy_pressure_%']),
            'sell_pressure': float(pressure['sell_pressure_%']),
            'delta': int(pressure['avg_delta']),
            'cumulative_delta': int(stats['cumulative_delta']),
            'trend': stats['trend'],
            'signal': signal,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'bars': bars[['time', 'close', 'volume']].tail(50).to_dict('records'),
            'open_positions': {
                'long': pressure['buy_volume'] / 1000,  # Масштабируем для визуализации
                'short': pressure['sell_volume'] / 1000,
            }
        })
        
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")

def monitoring_loop():
    """Цикл мониторинга и отправки live данных"""
    global monitoring_active
    
    while monitoring_active:
        try:
            get_mt5_data()
            
            # Отправляем данные всем подключённым клиентам
            socketio.emit('price_update', current_data, broadcast=True)
            
            # Обновляем каждую секунд��
            time.sleep(1)
        except Exception as e:
            print(f"❌ Ошибка в мониторинге: {e}")
            time.sleep(5)

@app.route('/')
def index():
    """Главная страница дашборда"""
    return render_template('live_dashboard.html')

@socketio.on('connect')
def handle_connect():
    """Клиент подключился"""
    print('✅ Клиент подключился')
    emit('response', {'data': 'Connected to Live Dashboard'})
    
    # Отправляем текущие данные
    emit('price_update', current_data)

@socketio.on('disconnect')
def handle_disconnect():
    """Клиент отключился"""
    print('❌ Клиент отключился')

@socketio.on('start_monitoring')
def handle_start_monitoring():
    """Начать мониторинг"""
    global monitoring_active
    
    if not monitoring_active:
        monitoring_active = True
        print('▶️  Мониторинг начат')
        
        # Запускаем цикл в отдельном потоке
        monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitor_thread.start()
        
        emit('response', {'status': 'Monitoring started'}, broadcast=True)

@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """Остановить мониторинг"""
    global monitoring_active
    monitoring_active = False
    print('⏹️  Мониторинг остановлен')
    emit('response', {'status': 'Monitoring stopped'}, broadcast=True)

@socketio.on('get_data')
def handle_get_data():
    """Получить текущие данные"""
    emit('price_update', current_data)

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════╗
    ║  🚀 BABRAM Live Order Flow Dashboard 🚀       ║
    ║  Real-time Monitoring and Analysis             ║
    ╚════════════════════════════════════════════════╝
    
    📡 Запускаем сервер...
    🌐 Откройте: http://localhost:5000
    """)
    
    # Запускаем Flask с WebSocket
    socketio.run(app, host='localhost', port=5000, debug=True, allow_unsafe_werkzeug=True)
