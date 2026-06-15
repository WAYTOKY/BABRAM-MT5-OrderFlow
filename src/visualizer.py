"""
Visualizer - Визуализация графиков Order Flow, Footprint, Delta
Создаёт интерактивные и статические графики
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.subplots as sp
from datetime import datetime
import os

class OrderFlowVisualizer:
    def __init__(self, output_dir="./output"):
        """
        Инициализация визуализатора
        
        Args:
            output_dir: Папка для сохранения графиков
        """
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def plot_order_flow(self, order_flow_df, title="Order Flow Analysis", show=True):
        """
        Создаёт график Order Flow с дельтой и кумулятивной дельтой
        
        Args:
            order_flow_df: DataFrame с Order Flow данными
            title: Название графика
            show: Показывать ли график
        """
        fig = sp.make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            subplot_titles=("Цена и объём", "Delta", "Cumulative Delta"),
            vertical_spacing=0.1
        )
        
        # График цены
        fig.add_trace(
            go.Scatter(
                x=order_flow_df['time'],
                y=order_flow_df['close'],
                name='Close',
                line=dict(color='blue', width=2),
                mode='lines'
            ),
            row=1, col=1
        )
        
        # График объёмов
        colors = ['green' if buy > 0 else 'red' for buy in order_flow_df['buy_volume']]
        fig.add_trace(
            go.Bar(
                x=order_flow_df['time'],
                y=order_flow_df['volume'],
                name='Volume',
                marker=dict(color=colors),
                opacity=0.6
            ),
            row=1, col=1
        )
        
        # График Delta
        colors_delta = ['green' if d > 0 else 'red' for d in order_flow_df['delta']]
        fig.add_trace(
            go.Bar(
                x=order_flow_df['time'],
                y=order_flow_df['delta'],
                name='Delta',
                marker=dict(color=colors_delta)
            ),
            row=2, col=1
        )
        
        # График кумулятивной дельты
        fig.add_trace(
            go.Scatter(
                x=order_flow_df['time'],
                y=order_flow_df['cumulative_delta'],
                name='Cumulative Delta',
                line=dict(color='purple', width=2),
                mode='lines'
            ),
            row=3, col=1
        )
        
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Delta", row=2, col=1)
        fig.update_yaxes(title_text="Cum. Delta", row=3, col=1)
        
        fig.update_layout(
            title_text=title,
            height=1000,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        filename = f"{self.output_dir}/order_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(filename)
        
        if show:
            fig.show()
        
        print(f"✅ График сохранён: {filename}")
        return fig
    
    def plot_footprint_heatmap(self, footprint_data, title="Footprint Heatmap", show=True):
        """
        Создаёт Heatmap Footprint
        
        Args:
            footprint_data: np.array с данными Footprint
            title: Название графика
            show: Показывать ли график
        """
        fig = go.Figure(data=go.Heatmap(
            z=footprint_data,
            colorscale='RdYlGn',
            name='Volume'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Candle #",
            yaxis_title="Price Level",
            height=600,
            template='plotly_dark'
        )
        
        filename = f"{self.output_dir}/footprint_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(filename)
        
        if show:
            fig.show()
        
        print(f"✅ Heatmap сохранён: {filename}")
        return fig
    
    def plot_buy_sell_pressure(self, order_flow_df, lookback=50, title="Buy/Sell Pressure", show=True):
        """
        Визуализирует давление покупателей и продавцов
        
        Args:
            order_flow_df: DataFrame с Order Flow
            lookback: Количество свечей
            title: Название графика
            show: Показывать ли график
        """
        # Рассчитываем скользящее давление
        recent = order_flow_df.tail(lookback).copy()
        
        buy_sum = []
        sell_sum = []
        
        for i in range(len(recent)):
            window = recent.iloc[:i+1]
            buy_sum.append(window['buy_volume'].sum())
            sell_sum.append(window['sell_volume'].sum())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=recent['time'],
            y=buy_sum,
            name='Cumulative Buy Volume',
            line=dict(color='green', width=2),
            mode='lines'
        ))
        
        fig.add_trace(go.Scatter(
            x=recent['time'],
            y=sell_sum,
            name='Cumulative Sell Volume',
            line=dict(color='red', width=2),
            mode='lines'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Cumulative Volume",
            height=500,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        filename = f"{self.output_dir}/buy_sell_pressure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(filename)
        
        if show:
            fig.show()
        
        print(f"✅ График давления сохранён: {filename}")
        return fig
    
    def plot_delta_momentum(self, delta_df, title="Delta Momentum", show=True):
        """
        Визуализирует момент дельты (ускорение)
        
        Args:
            delta_df: DataFrame с Delta данными
            title: Название графика
            show: Показывать ли график
        """
        fig = sp.make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            subplot_titles=("Delta", "Delta Momentum"),
            vertical_spacing=0.15
        )
        
        # Delta
        colors = ['green' if d > 0 else 'red' for d in delta_df['delta']]
        fig.add_trace(
            go.Bar(
                x=delta_df['time'],
                y=delta_df['delta'],
                name='Delta',
                marker=dict(color=colors),
                opacity=0.7
            ),
            row=1, col=1
        )
        
        # Delta MA
        fig.add_trace(
            go.Scatter(
                x=delta_df['time'],
                y=delta_df['delta_ma'],
                name='Delta MA',
                line=dict(color='blue', width=2),
                mode='lines'
            ),
            row=1, col=1
        )
        
        # Delta Momentum
        colors_momentum = ['green' if m > 0 else 'red' for m in delta_df['delta_momentum']]
        fig.add_trace(
            go.Bar(
                x=delta_df['time'],
                y=delta_df['delta_momentum'],
                name='Momentum',
                marker=dict(color=colors_momentum),
                opacity=0.7
            ),
            row=2, col=1
        )
        
        fig.update_yaxes(title_text="Delta", row=1, col=1)
        fig.update_yaxes(title_text="Momentum", row=2, col=1)
        
        fig.update_layout(
            title=title,
            height=800,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        filename = f"{self.output_dir}/delta_momentum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(filename)
        
        if show:
            fig.show()
        
        print(f"✅ График momentum сохранён: {filename}")
        return fig
    
    def plot_combined_analysis(self, bars_df, order_flow_df, delta_df, 
                               title="Combined Order Flow & Delta Analysis", show=True):
        """
        Создаёт комбинированный график со всеми индикаторами
        
        Args:
            bars_df: DataFrame с OHLCV
            order_flow_df: DataFrame с Order Flow
            delta_df: DataFrame с Delta
            title: Название графика
            show: Показывать ли график
        """
        fig = sp.make_subplots(
            rows=5, cols=1,
            shared_xaxes=True,
            subplot_titles=(
                "Price & Volume",
                "Order Flow Signal",
                "Delta",
                "Cumulative Delta",
                "Pressure %"
            ),
            vertical_spacing=0.08,
            row_heights=[0.25, 0.15, 0.15, 0.15, 0.3]
        )
        
        # 1. Candlestick + Volume
        fig.add_trace(
            go.Candlestick(
                x=bars_df['time'],
                open=bars_df['open'],
                high=bars_df['high'],
                low=bars_df['low'],
                close=bars_df['close'],
                name='GOLD'
            ),
            row=1, col=1
        )
        
        vol_colors = ['green' if close > open_ else 'red' 
                      for close, open_ in zip(bars_df['close'], bars_df['open'])]
        fig.add_trace(
            go.Bar(
                x=bars_df['time'],
                y=bars_df['volume'],
                name='Volume',
                marker=dict(color=vol_colors),
                opacity=0.3
            ),
            row=1, col=1
        )
        
        # 2. Order Flow Signal
        colors_of = ['green' if sig == 'LONG' else 'red' 
                     for sig in order_flow_df['of_signal']]
        fig.add_trace(
            go.Bar(
                x=order_flow_df['time'],
                y=order_flow_df['delta'],
                name='OF Signal',
                marker=dict(color=colors_of),
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # 3. Delta
        colors_delta = ['green' if d > 0 else 'red' for d in delta_df['delta']]
        fig.add_trace(
            go.Bar(
                x=delta_df['time'],
                y=delta_df['delta'],
                name='Delta',
                marker=dict(color=colors_delta),
                opacity=0.7
            ),
            row=3, col=1
        )
        
        # 4. Cumulative Delta
        fig.add_trace(
            go.Scatter(
                x=delta_df['time'],
                y=delta_df['cumulative_delta'],
                name='Cum Delta',
                line=dict(color='purple', width=2),
                mode='lines'
            ),
            row=4, col=1
        )
        
        # 5. Buy/Sell Pressure
        total_buy = order_flow_df['buy_volume'].sum()
        total_sell = order_flow_df['sell_volume'].sum()
        total = total_buy + total_sell
        
        if total > 0:
            buy_pressure = (total_buy / total) * 100
            sell_pressure = (total_sell / total) * 100
            
            fig.add_trace(
                go.Bar(
                    x=['Buy', 'Sell'],
                    y=[buy_pressure, sell_pressure],
                    marker=dict(color=['green', 'red']),
                    text=[f"{buy_pressure:.1f}%", f"{sell_pressure:.1f}%"],
                    textposition='auto'
                ),
                row=5, col=1
            )
        
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="OF", row=2, col=1)
        fig.update_yaxes(title_text="Delta", row=3, col=1)
        fig.update_yaxes(title_text="Cum Δ", row=4, col=1)
        fig.update_yaxes(title_text="Pressure %", row=5, col=1)
        
        fig.update_layout(
            title=title,
            height=1400,
            hovermode='x unified',
            template='plotly_dark'
        )
        
        filename = f"{self.output_dir}/combined_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(filename)
        
        if show:
            fig.show()
        
        print(f"✅ Комбинированный график сохранён: {filename}")
        return fig


if __name__ == "__main__":
    # Пример использования
    from mt5_connector import MT5Connector
    from order_flow import OrderFlowAnalyzer
    from delta_analyzer import DeltaAnalyzer
    
    connector = MT5Connector(symbol="GOLD", timeframe=1)
    bars = connector.get_bars(num_bars=300)
    
    of_analyzer = OrderFlowAnalyzer(bars)
    delta_analyzer = DeltaAnalyzer(bars)
    
    visualizer = OrderFlowVisualizer()
    
    # Создаём графики
    visualizer.plot_order_flow(of_analyzer.get_order_flow(), show=False)
    visualizer.plot_delta_momentum(delta_analyzer.get_delta_data(), show=False)
    visualizer.plot_combined_analysis(bars, of_analyzer.get_order_flow(), 
                                      delta_analyzer.get_delta_data(), show=False)
    
    print("\n✅ Все графики созданы!")
    
    connector.disconnect()
