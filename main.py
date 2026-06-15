"""
BABRAM MT5 Order Flow Analyzer
Главный скрипт для анализа потока ордеров и создания индикаторов Footprint/Delta
"""
import sys
import os
from src.mt5_connector import MT5Connector
from src.order_flow import OrderFlowAnalyzer
from src.footprint import FootprintAnalyzer
from src.delta_analyzer import DeltaAnalyzer
from src.visualizer import OrderFlowVisualizer
from datetime import datetime

def print_header():
    """Печатает красивый заголовок"""
    print("\n" + "="*60)
    print("  🚀 BABRAM MT5 Order Flow Analyzer 🚀".center(60))
    print("  Advanced Trading Indicators & Analysis".center(60))
    print("="*60 + "\n")

def print_section(title):
    """Печатает заголовок секции"""
    print(f"\n{'─'*60}")
    print(f"📊 {title}")
    print(f"{'─'*60}")

def main():
    """Главная функция"""
    print_header()
    
    # Параметры анализа
    SYMBOL = "GOLD"
    TIMEFRAME_1 = 1  # 1 минута
    TIMEFRAME_5 = 5  # 5 минут
    NUM_BARS = 500
    
    print(f"⚙️  Параметры анализа:")
    print(f"   • Инструмент: {SYMBOL}")
    print(f"   • Таймфреймы: {TIMEFRAME_1}м и {TIMEFRAME_5}м")
    print(f"   • Количество свечей: {NUM_BARS}")
    
    # ============ 1М АНАЛИЗ ============
    print_section("Анализ на 1 минутном таймфрейме (1М)")
    
    # Подключаемся к MT5 (1M)
    connector_1m = MT5Connector(symbol=SYMBOL, timeframe=TIMEFRAME_1)
    if not connector_1m.connected:
        print("❌ Ошибка подключения к MT5!")
        return
    
    # Получаем свечи
    print("📥 Получение свечей...")
    bars_1m = connector_1m.get_bars(num_bars=NUM_BARS)
    if bars_1m is None:
        print("❌ Не удалось получить данные!")
        connector_1m.disconnect()
        return
    
    print(f"✅ Получено {len(bars_1m)} свечей")
    print(f"   Период: {bars_1m['time'].min()} → {bars_1m['time'].max()}")
    
    # Информация о символе
    symbol_info = connector_1m.get_symbol_info()
    if symbol_info:
        print(f"\n📈 Информация о {SYMBOL}:")
        print(f"   Bid: {symbol_info['bid']}")
        print(f"   Ask: {symbol_info['ask']}")
        print(f"   Spread: {symbol_info['ask'] - symbol_info['bid']}")
    
    # Order Flow анализ (1M)
    print("\n🔄 Анализ потока ордеров...")
    of_analyzer_1m = OrderFlowAnalyzer(bars_1m)
    of_data_1m = of_analyzer_1m.get_order_flow()
    
    pressure_1m = of_analyzer_1m.get_buy_sell_pressure(lookback=20)
    print(f"\n💪 Давление покупателей/продавцов (последние 20 свечей):")
    print(f"   Buy Volume: {pressure_1m['buy_volume']:.0f}")
    print(f"   Sell Volume: {pressure_1m['sell_volume']:.0f}")
    print(f"   Buy Pressure: {pressure_1m['buy_pressure_%']}%")
    print(f"   Sell Pressure: {pressure_1m['sell_pressure_%']}%")
    print(f"   Доминирует: {pressure_1m['dominant']}")
    
    signals_1m = of_analyzer_1m.detect_signal(strength_threshold=5000)
    print(f"\n⚡ Сильные сигналы Order Flow (последние 5):")
    for signal in signals_1m[-5:]:
        print(f"   {signal['time']} | {signal['type']} | Delta: {signal['delta']:.0f}")
    
    # Delta анализ (1M)
    print("\n📊 Анализ Delta...")
    delta_analyzer_1m = DeltaAnalyzer(bars_1m, moving_avg_period=20)
    delta_data_1m = delta_analyzer_1m.get_delta_data()
    
    div_analysis_1m = delta_analyzer_1m.analyze_delta_divergence(lookback=20)
    print(f"\n🔄 Анализ расхождения (divergence):")
    print(f"   Изменение цены: {div_analysis_1m['price_change']}")
    print(f"   Изменение дельты: {div_analysis_1m['delta_change']:.0f}")
    print(f"   Тип: {div_analysis_1m['divergence']}")
    
    stats_1m = delta_analyzer_1m.get_delta_statistics(lookback=100)
    print(f"\n📈 Статистика Delta (последние 100 свечей):")
    print(f"   Средняя дельта: {stats_1m['mean_delta']:.0f}")
    print(f"   Макс/Мин дельта: {stats_1m['max_delta']:.0f} / {stats_1m['min_delta']:.0f}")
    print(f"   Позитивных свечей: {stats_1m['positive_bars']}")
    print(f"   Негативных свечей: {stats_1m['negative_bars']}")
    print(f"   Тренд дельты: {stats_1m['trend']}")
    
    # Footprint анализ (1M)
    print("\n🎯 Анализ Footprint...")
    fp_analyzer_1m = FootprintAnalyzer(bars_1m, price_levels=20)
    candle_analysis = fp_analyzer_1m.analyze_candle_structure()
    
    print(f"\n📊 Структура последней свечи (1M):")
    print(f"   Open: {candle_analysis['open']}")
    print(f"   Close: {candle_analysis['close']}")
    print(f"   High: {candle_analysis['high']}")
    print(f"   Low: {candle_analysis['low']}")
    print(f"   Total Volume: {candle_analysis['total_volume']:.0f}")
    print(f"   Buy Volume: {candle_analysis['total_buy_volume']:.0f}")
    print(f"   Sell Volume: {candle_analysis['total_sell_volume']:.0f}")
    print(f"   Buy Pressure: {candle_analysis['buy_pressure_%']}%")
    print(f"   Sell Pressure: {candle_analysis['sell_pressure_%']}%")
    
    clusters = fp_analyzer_1m.detect_volume_cluster(threshold_percentile=80)
    print(f"\n🔥 Объёмные кластеры: {len(clusters)} найдено")
    
    # ============ 5М АНАЛИЗ ============
    print_section("Анализ на 5 минутном таймфрейме (5M)")
    
    connector_5m = MT5Connector(symbol=SYMBOL, timeframe=TIMEFRAME_5)
    bars_5m = connector_5m.get_bars(num_bars=NUM_BARS)
    
    if bars_5m is not None:
        print(f"✅ Получено {len(bars_5m)} свечей")
        print(f"   Период: {bars_5m['time'].min()} → {bars_5m['time'].max()}")
        
        # Order Flow (5M)
        of_analyzer_5m = OrderFlowAnalyzer(bars_5m)
        pressure_5m = of_analyzer_5m.get_buy_sell_pressure(lookback=20)
        
        print(f"\n💪 Давление на 5M:")
        print(f"   Buy Pressure: {pressure_5m['buy_pressure_%']}%")
        print(f"   Sell Pressure: {pressure_5m['sell_pressure_%']}%")
        print(f"   Доминирует: {pressure_5m['dominant']}")
        
        # Delta (5M)
        delta_analyzer_5m = DeltaAnalyzer(bars_5m, moving_avg_period=20)
        stats_5m = delta_analyzer_5m.get_delta_statistics(lookback=100)
        
        print(f"\n📈 Delta на 5M:")
        print(f"   Тренд: {stats_5m['trend']}")
        print(f"   Средняя дельта: {stats_5m['mean_delta']:.0f}")
        print(f"   Кумулятивная дельта: {stats_5m['cumulative_delta']:.0f}")
    
    # ============ ВИЗУАЛИЗАЦИЯ ============
    print_section("Создание графиков и визуализации")
    
    visualizer = OrderFlowVisualizer(output_dir="./output")
    
    print("\n📊 Создание графиков...")
    print("   1. Order Flow анализ...")
    visualizer.plot_order_flow(of_analyzer_1m.get_order_flow(), 
                               title=f"{SYMBOL} Order Flow Analysis (1M)", show=False)
    
    print("   2. Buy/Sell Pressure...")
    visualizer.plot_buy_sell_pressure(of_analyzer_1m.get_order_flow(),
                                     title=f"{SYMBOL} Buy/Sell Pressure (1M)", show=False)
    
    print("   3. Delta Momentum...")
    visualizer.plot_delta_momentum(delta_analyzer_1m.get_delta_data(),
                                  title=f"{SYMBOL} Delta Momentum (1M)", show=False)
    
    print("   4. Footprint Heatmap...")
    heatmap_data = fp_analyzer_1m.get_heatmap_data(bars_count=50)
    visualizer.plot_footprint_heatmap(heatmap_data,
                                     title=f"{SYMBOL} Footprint Heatmap (1M)", show=False)
    
    print("   5. Комбинированный анализ...")
    visualizer.plot_combined_analysis(bars_1m, of_analyzer_1m.get_order_flow(),
                                     delta_analyzer_1m.get_delta_data(),
                                     title=f"{SYMBOL} Combined Analysis (1M)", show=False)
    
    print(f"\n✅ Все графики созданы в папке: ./output")
    
    # ============ ОБЩИЕ ВЫВОДЫ ============
    print_section("Общие выводы")
    
    print("\n📋 Сводка анализа:")
    print(f"\n1M таймфрейм:")
    print(f"   • Order Flow тренд: {pressure_1m['dominant']}")
    print(f"   • Delta тренд: {stats_1m['trend']}")
    print(f"   • Divergence: {div_analysis_1m['divergence']}")
    
    if bars_5m is not None:
        print(f"\n5M таймфрейм:")
        print(f"   • Order Flow тренд: {pressure_5m['dominant']}")
        print(f"   • Delta тренд: {stats_5m['trend']}")
    
    print("\n💡 Рекомендации:")
    if pressure_1m['dominant'] == 'BUYERS' and stats_1m['trend'] == 'BULLISH':
        print("   ✅ Сильный бычий тренд - рассмотрите LONG позиции")
    elif pressure_1m['dominant'] == 'SELLERS' and stats_1m['trend'] == 'BEARISH':
        print("   ❌ Сильный медвежий тренд - рассмотрите SHORT позиции")
    else:
        print("   ⚠️  Тренды не согласованы - ждите подтверждения")
    
    # Отключаемся
    print("\n" + "="*60)
    connector_1m.disconnect()
    connector_5m.disconnect()
    
    print("✅ Анализ завершён!\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
