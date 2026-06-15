"""
MT5 Connector - Подключение к MetaTrader 5 и получение данных
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import pytz

class MT5Connector:
    def __init__(self, symbol="GOLD", timeframe=1):
        """
        Инициализация подключения к MT5
        
        Args:
            symbol: Инструмент (GOLD, EURUSD и т.д.)
            timeframe: Таймфрейм в минутах (1, 5, 15, 60 и т.д.)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.connected = False
        
        # Инициализируем MT5
        if not mt5.initialize():
            print("❌ Ошибка инициализации MT5!")
            print(f"Ошибка: {mt5.last_error()}")
            return
        
        self.connected = True
        print("✅ MT5 инициализирован успешно!")
        print(f"Версия MT5: {mt5.version()}")
    
    def get_bars(self, num_bars=1000):
        """
        Получить свечи с MT5
        
        Args:
            num_bars: Количество свечей для получения
            
        Returns:
            DataFrame с OHLCV данными
        """
        if not self.connected:
            print("❌ MT5 не инициализирован!")
            return None
        
        # Получаем свечи
        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            60: mt5.TIMEFRAME_H1,
        }
        
        tf = timeframe_map.get(self.timeframe, mt5.TIMEFRAME_M1)
        
        bars = mt5.copy_rates_from_pos(self.symbol, tf, 0, num_bars)
        
        if bars is None:
            print(f"❌ Ошибка получения данных для {self.symbol}")
            return None
        
        # Конвертируем в DataFrame
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
        df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
        
        return df
    
    def get_ticks(self, num_ticks=10000):
        """
        Получить тики (все сделки) для анализа потока ордеров
        
        Args:
            num_ticks: Количество тиков
            
        Returns:
            DataFrame с тиками
        """
        if not self.connected:
            print("❌ MT5 не инициализирован!")
            return None
        
        # Получаем последние тики
        ticks = mt5.copy_ticks_from_pos(self.symbol, 0, num_ticks, mt5.TICKS_ALL)
        
        if ticks is None:
            print(f"❌ Ошибка получения тиков для {self.symbol}")
            return None
        
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df[['time', 'bid', 'ask', 'last', 'volume', 'volume_real', 'flags']]
        
        return df
    
    def get_symbol_info(self):
        """
        Получить информацию о символе
        
        Returns:
            dict с информацией о символе
        """
        if not self.connected:
            return None
        
        info = mt5.symbol_info(self.symbol)
        if info is None:
            print(f"❌ Символ {self.symbol} не найден!")
            return None
        
        return {
            'name': info.name,
            'bid': info.bid,
            'ask': info.ask,
            'point': info.point,
            'digits': info.digits,
            'bid_high': info.bid_high,
            'bid_low': info.bid_low,
            'ask_high': info.ask_high,
            'ask_low': info.ask_low,
        }
    
    def disconnect(self):
        """Отключиться от MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("✅ MT5 отключен")


if __name__ == "__main__":
    # Пример использования
    connector = MT5Connector(symbol="GOLD", timeframe=1)
    
    # Получить свечи
    bars = connector.get_bars(num_bars=100)
    if bars is not None:
        print("\n📊 Последние 5 свечей:")
        print(bars.tail())
    
    # Получить информацию о символе
    info = connector.get_symbol_info()
    if info:
        print(f"\n📈 Информация о {connector.symbol}:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    connector.disconnect()
