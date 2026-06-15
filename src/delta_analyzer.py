"""
Delta Analyzer - Анализ дельты (разница между объёмами покупок и продаж)
Показывает силу тренда и изменения в давлении
"""
import pandas as pd
import numpy as np

class DeltaAnalyzer:
    def __init__(self, bars_df, moving_avg_period=20):
        """
        Инициализация анализатора дельты
        
        Args:
            bars_df: DataFrame с OHLCV данными
            moving_avg_period: Период для скользящей средней дельты
        """
        self.bars = bars_df.copy()
        self.ma_period = moving_avg_period
        self.delta_data = self._calculate_delta()
    
    def _calculate_delta(self):
        """
        Рассчитывает Delta для каждой свечи
        
        Returns:
            DataFrame с Delta данными
        """
        df = self.bars.copy()
        
        # Определяем направление свечи
        df['direction'] = df['close'].diff()
        df['is_up'] = df['direction'] > 0
        df['is_down'] = df['direction'] < 0
        
        # Рассчитываем объёмы покупок и продаж
        df['buy_volume'] = df['volume'].where(df['is_up'], 0)
        df['sell_volume'] = df['volume'].where(df['is_down'], 0)
        
        # Дельта = Объём покупок - Объём продаж
        df['delta'] = df['buy_volume'] - df['sell_volume']
        
        # Кумулятивная дельта
        df['cumulative_delta'] = df['delta'].cumsum()
        
        # Скользящая средняя дельты
        df['delta_ma'] = df['delta'].rolling(window=self.ma_period).mean()
        
        # Абсолютная дельта (сила)
        df['delta_abs'] = abs(df['delta'])
        
        # Усреднённая абсолютная дельта
        df['delta_abs_ma'] = df['delta_abs'].rolling(window=self.ma_period).mean()
        
        # Дельта наклон (ускорение)
        df['delta_momentum'] = df['delta'].diff()
        
        return df[['time', 'close', 'volume', 'buy_volume', 'sell_volume', 
                   'delta', 'cumulative_delta', 'delta_ma', 'delta_abs', 
                   'delta_abs_ma', 'delta_momentum']]
    
    def get_delta_data(self):
        """Получить данные дельты"""
        return self.delta_data
    
    def get_cumulative_delta(self):
        """Получить кумулятивную дельту"""
        return self.delta_data[['time', 'cumulative_delta']]
    
    def analyze_delta_divergence(self, lookback=20):
        """
        Анализирует расхождение дельты с ценой (divergence)
        Если цена растёт, а дельта падает - это бычье расхождение
        
        Args:
            lookback: Количество свечей для анализа
            
        Returns:
            Dict с информацией о расхождении
        """
        recent = self.delta_data.tail(lookback)
        
        price_higher = recent['close'].iloc[-1] > recent['close'].iloc[0]
        delta_higher = recent['cumulative_delta'].iloc[-1] > recent['cumulative_delta'].iloc[0]
        
        divergence = None
        if price_higher and not delta_higher:
            divergence = 'BEARISH DIVERGENCE'  # Цена выше, дельта ниже
        elif not price_higher and delta_higher:
            divergence = 'BULLISH DIVERGENCE'  # Цена ниже, дельта выше
        else:
            divergence = 'NO DIVERGENCE'  # Согласованное движение
        
        return {
            'price_change': round(recent['close'].iloc[-1] - recent['close'].iloc[0], 2),
            'delta_change': round(recent['cumulative_delta'].iloc[-1] - recent['cumulative_delta'].iloc[0], 0),
            'divergence': divergence,
            'current_delta': round(recent['delta'].iloc[-1], 0),
            'delta_ma': round(recent['delta_ma'].iloc[-1], 0),
        }
    
    def detect_delta_extremes(self, threshold_percentile=95):
        """
        Обнаруживает экстремальные значения дельты
        
        Args:
            threshold_percentile: Процентиль для определения экстремума
            
        Returns:
            List с экстремальными значениями
        """
        extremes = []
        
        # Находим пороги
        delta_abs_values = self.delta_data['delta_abs'].dropna()
        upper_threshold = np.percentile(delta_abs_values, threshold_percentile)
        
        for idx, row in self.delta_data.iterrows():
            if pd.notna(row['delta_abs']) and row['delta_abs'] >= upper_threshold:
                extremes.append({
                    'time': row['time'],
                    'price': row['close'],
                    'delta': row['delta'],
                    'type': 'EXTREME BUY' if row['delta'] > 0 else 'EXTREME SELL',
                    'strength': row['delta_abs']
                })
        
        return extremes
    
    def get_delta_trend(self, lookback=50):
        """
        Определяет тренд дельты
        
        Args:
            lookback: Количество свечей для анализа
            
        Returns:
            str - 'BULLISH', 'BEARISH', 'NEUTRAL'
        """
        recent = self.delta_data.tail(lookback)
        avg_delta = recent['delta'].mean()
        
        if avg_delta > 0:
            return 'BULLISH'
        elif avg_delta < 0:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def get_delta_statistics(self, lookback=100):
        """
        Получить статистику дельты
        
        Args:
            lookback: Количество свечей
            
        Returns:
            Dict со статистикой
        """
        recent = self.delta_data.tail(lookback)
        
        return {
            'mean_delta': round(recent['delta'].mean(), 0),
            'std_delta': round(recent['delta'].std(), 0),
            'max_delta': round(recent['delta'].max(), 0),
            'min_delta': round(recent['delta'].min(), 0),
            'sum_delta': round(recent['delta'].sum(), 0),
            'cumulative_delta': round(recent['cumulative_delta'].iloc[-1], 0),
            'positive_bars': len(recent[recent['delta'] > 0]),
            'negative_bars': len(recent[recent['delta'] < 0]),
            'trend': self.get_delta_trend(lookback)
        }


if __name__ == "__main__":
    # Пример использования
    from mt5_connector import MT5Connector
    
    connector = MT5Connector(symbol="GOLD", timeframe=1)
    bars = connector.get_bars(num_bars=500)
    
    analyzer = DeltaAnalyzer(bars, moving_avg_period=20)
    
    print("📊 Delta Analysis:")
    print(analyzer.delta_data.tail(10))
    
    print("\n🔄 Divergence Analysis (последние 20 свечей):")
    divergence = analyzer.analyze_delta_divergence(lookback=20)
    for key, value in divergence.items():
        print(f"  {key}: {value}")
    
    print("\n📈 Statistics (последние 100 свечей):")
    stats = analyzer.get_delta_statistics(lookback=100)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n⚡ Экстремальные значения дельты:")
    extremes = analyzer.detect_delta_extremes(threshold_percentile=95)
    for extreme in extremes[-5:]:
        print(f"  {extreme['time']} | {extreme['type']} | Delta: {extreme['delta']}")
    
    connector.disconnect()
