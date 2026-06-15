"""
Footprint Analyzer - Создание Footprint графиков
Показывает объёмы на каждом ценовом уровне в свече
"""
import pandas as pd
import numpy as np

class FootprintAnalyzer:
    def __init__(self, bars_df, price_levels=20):
        """
        Инициализация анализатора Footprint
        
        Args:
            bars_df: DataFrame с OHLCV данными
            price_levels: Количество ценовых уровней для Footprint
        """
        self.bars = bars_df.copy()
        self.price_levels = price_levels
        self.footprint = self._build_footprint()
    
    def _build_footprint(self):
        """
        Строит Footprint данные для каждой свечи
        
        Returns:
            Dict с Footprint информацией
        """
        footprint_data = []
        
        for idx, bar in self.bars.iterrows():
            # Определяем ценовые уровни в свече
            high = bar['high']
            low = bar['low']
            close = bar['close']
            volume = bar['volume']
            
            # Шаг цены
            price_range = high - low
            if price_range == 0:
                price_range = 0.001  # Чтобы не было деления на ноль
            
            step = price_range / self.price_levels
            
            # Определяем объёмы на каждом уровне
            # Проще: распределяем объём пропорционально положению цены
            levels = []
            for level in range(self.price_levels):
                price = low + (step * level)
                
                # Определяем объём на этом уровне
                # Если цена выше close - это давление продавцов (RED)
                # Если цена ниже close - это давление покупателей (GREEN)
                if price <= close:
                    level_volume = (volume / self.price_levels) * (1 + (close - price) / price_range)
                    level_type = 'BUY'
                else:
                    level_volume = (volume / self.price_levels) * (1 - (price - close) / price_range)
                    level_type = 'SELL'
                
                levels.append({
                    'price': round(price, 2),
                    'volume': max(0, round(level_volume, 0)),
                    'type': level_type
                })
            
            footprint_data.append({
                'time': bar['time'],
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'total_volume': volume,
                'levels': levels
            })
        
        return footprint_data
    
    def get_footprint(self):
        """Получить Footprint данные"""
        return self.footprint
    
    def get_heatmap_data(self, bars_count=50):
        """
        Получить данные для Heatmap (матрица объёмов)
        
        Args:
            bars_count: Количество свечей для отображения
            
        Returns:
            np.array для визуализации
        """
        recent_fp = self.footprint[-bars_count:]
        
        # Создаём матрицу: строки = ценовые уровни, столбцы = свечи
        matrix = np.zeros((self.price_levels, len(recent_fp)))
        
        for col, fp in enumerate(recent_fp):
            for row, level in enumerate(fp['levels']):
                matrix[row, col] = level['volume']
        
        return matrix
    
    def analyze_candle_structure(self, bar_index=-1):
        """
        Анализирует структуру отдельной свечи
        
        Args:
            bar_index: Индекс свечи (по умолчанию последняя)
            
        Returns:
            Dict с анализом
        """
        if bar_index >= len(self.footprint):
            return None
        
        fp = self.footprint[bar_index]
        levels = fp['levels']
        
        # Находим уровни с максимальным объёмом
        buy_levels = [l for l in levels if l['type'] == 'BUY']
        sell_levels = [l for l in levels if l['type'] == 'SELL']
        
        max_buy = max(buy_levels, key=lambda x: x['volume']) if buy_levels else None
        max_sell = max(sell_levels, key=lambda x: x['volume']) if sell_levels else None
        
        total_buy_vol = sum(l['volume'] for l in buy_levels)
        total_sell_vol = sum(l['volume'] for l in sell_levels)
        
        return {
            'time': fp['time'],
            'open': fp['open'],
            'close': fp['close'],
            'high': fp['high'],
            'low': fp['low'],
            'total_volume': fp['total_volume'],
            'total_buy_volume': round(total_buy_vol, 0),
            'total_sell_volume': round(total_sell_vol, 0),
            'max_buy_level': max_buy,
            'max_sell_level': max_sell,
            'buy_pressure_%': round((total_buy_vol / fp['total_volume'] * 100), 2) if fp['total_volume'] > 0 else 0,
            'sell_pressure_%': round((total_sell_vol / fp['total_volume'] * 100), 2) if fp['total_volume'] > 0 else 0
        }
    
    def detect_volume_cluster(self, threshold_percentile=75):
        """
        Обнаруживает скопления объёмов (важные уровни поддержки/сопротивления)
        
        Args:
            threshold_percentile: Процентиль для определения значимого объёма
            
        Returns:
            List с обнаруженными кластерами
        """
        clusters = []
        
        for fp in self.footprint:
            all_volumes = [level['volume'] for level in fp['levels']]
            threshold = np.percentile(all_volumes, threshold_percentile)
            
            significant_levels = [
                level for level in fp['levels'] 
                if level['volume'] >= threshold
            ]
            
            if significant_levels:
                clusters.append({
                    'time': fp['time'],
                    'levels': significant_levels,
                    'count': len(significant_levels)
                })
        
        return clusters


if __name__ == "__main__":
    # Пример использования
    from mt5_connector import MT5Connector
    
    connector = MT5Connector(symbol="GOLD", timeframe=1)
    bars = connector.get_bars(num_bars=100)
    
    analyzer = FootprintAnalyzer(bars, price_levels=20)
    
    print("📊 Footprint Analysis - Последняя свеча:")
    last_candle = analyzer.analyze_candle_structure()
    for key, value in last_candle.items():
        print(f"  {key}: {value}")
    
    print("\n🔥 Объёмные кластеры:")
    clusters = analyzer.detect_volume_cluster(threshold_percentile=80)
    for cluster in clusters[-5:]:
        print(f"  {cluster['time']} | Кластеры: {cluster['count']}")
    
    connector.disconnect()
