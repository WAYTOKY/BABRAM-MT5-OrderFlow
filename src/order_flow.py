"""
Order Flow Analyzer - Анализ потока ордеров
Определяет давление покупателей vs продавцов
"""
import pandas as pd
import numpy as np
from datetime import datetime

class OrderFlowAnalyzer:
    def __init__(self, bars_df):
        """
        Инициализация анализатора потока ордеров
        
        Args:
            bars_df: DataFrame с OHLCV данными от MT5
        """
        self.bars = bars_df.copy()
        self.order_flow = self._calculate_order_flow()
    
    def _calculate_order_flow(self):
        """
        Рассчитывает Order Flow для каждой свечи
        Order Flow показывает агрессивные покупки vs продажи
        
        Returns:
            DataFrame с Order Flow данными
        """
        df = self.bars.copy()
        
        # Рассчитываем направление движения цены
        df['close_diff'] = df['close'].diff()
        df['up'] = df['close_diff'] > 0
        df['down'] = df['close_diff'] < 0
        
        # Рассчитываем объём покупок и продаж
        # Если свеча вверх - объём считается покупками
        # Если свеча вниз - объём считается продажами
        df['buy_volume'] = df['volume'].where(df['up'], 0)
        df['sell_volume'] = df['volume'].where(df['down'], 0)
        
        # Delta = Buy Volume - Sell Volume
        df['delta'] = df['buy_volume'] - df['sell_volume']
        
        # Cumulative Delta
        df['cumulative_delta'] = df['delta'].cumsum()
        
        # Order Flow сигнал
        # Положительный delta = давление покупателей (LONG)
        # Отрицательный delta = давление продавцов (SHORT)
        df['of_signal'] = df['delta'].apply(lambda x: 'LONG' if x > 0 else ('SHORT' if x < 0 else 'NEUTRAL'))
        
        return df[['time', 'close', 'volume', 'buy_volume', 'sell_volume', 'delta', 'cumulative_delta', 'of_signal']]
    
    def get_order_flow(self):
        """Получить данные Order Flow"""
        return self.order_flow
    
    def get_cumulative_delta(self):
        """Получить кумулятивную дельту"""
        return self.order_flow[['time', 'cumulative_delta']]
    
    def get_buy_sell_pressure(self, lookback=20):
        """
        Анализ давления покупателей/продавцов за последний период
        
        Args:
            lookback: Количество свечей для анализа
            
        Returns:
            dict с показателями давления
        """
        recent = self.order_flow.tail(lookback)
        
        total_buy = recent['buy_volume'].sum()
        total_sell = recent['sell_volume'].sum()
        total_volume = recent['volume'].sum()
        
        if total_volume == 0:
            return None
        
        buy_pressure = (total_buy / total_volume) * 100
        sell_pressure = (total_sell / total_volume) * 100
        
        return {
            'buy_volume': total_buy,
            'sell_volume': total_sell,
            'buy_pressure_%': round(buy_pressure, 2),
            'sell_pressure_%': round(sell_pressure, 2),
            'avg_delta': round(recent['delta'].mean(), 2),
            'dominant': 'BUYERS' if buy_pressure > sell_pressure else 'SELLERS'
        }
    
    def detect_signal(self, strength_threshold=1000):
        """
        Детектирует сильные сигналы Order Flow
        
        Args:
            strength_threshold: Минимальная сила сигнала (дельта)
            
        Returns:
            List с сигналами
        """
        signals = []
        
        for idx, row in self.order_flow.iterrows():
            if abs(row['delta']) > strength_threshold:
                signal = {
                    'time': row['time'],
                    'price': row['close'],
                    'delta': row['delta'],
                    'type': 'STRONG BUY' if row['delta'] > 0 else 'STRONG SELL',
                    'strength': abs(row['delta'])
                }
                signals.append(signal)
        
        return signals


if __name__ == "__main__":
    # Пример использования
    from mt5_connector import MT5Connector
    
    connector = MT5Connector(symbol="GOLD", timeframe=1)
    bars = connector.get_bars(num_bars=500)
    
    analyzer = OrderFlowAnalyzer(bars)
    
    print("📊 Order Flow Analysis:")
    print(analyzer.order_flow.tail(10))
    
    print("\n💪 Buy/Sell Pressure (последние 20 свечей):")
    pressure = analyzer.get_buy_sell_pressure(lookback=20)
    for key, value in pressure.items():
        print(f"  {key}: {value}")
    
    print("\n⚡ Сильные сигналы:")
    signals = analyzer.detect_signal(strength_threshold=5000)
    for signal in signals[-5:]:
        print(f"  {signal['time']} | {signal['type']} | Delta: {signal['delta']}")
    
    connector.disconnect()
