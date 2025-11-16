import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

data = pd.read_csv("benchmark_results.csv")

# Convertir latencia de segundos a milisegundos para mejor visualización
data['latencia_ms'] = data['mean_latency_success_s'] * 1000

# Crear figura con 2 subgráficos
fig, axes = plt.subplots(1, 2, figsize=(15, 5))

# Gráfico 1: Tiempo total vs Threads (Escalabilidad)
axes[0].plot(data["threads"], data["time_seconds"], marker='o', linewidth=2, markersize=8, color='blue')
axes[0].set_title("Escalabilidad de TiDB\nTiempo Total vs Número de Hilos", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Número de hilos (transacciones concurrentes)", fontsize=11)
axes[0].set_ylabel("Tiempo total (segundos)", fontsize=11)
axes[0].grid(True, alpha=0.3)

# Añadir valores en los puntos
for i, row in data.iterrows():
    axes[0].annotate(f'{row["time_seconds"]:.1f}s', 
                    xy=(row['threads'], row['time_seconds']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

# Gráfico 2: Latencia promedio por transacción (mean_latency_success_s)
axes[1].plot(data["threads"], data['latencia_ms'], marker='s', linewidth=2, markersize=8, color='green')
axes[1].set_title("Latencia Promedio por Transacción\n(Transacciones Exitosas)", fontsize=12, fontweight='bold')
axes[1].set_xlabel("Número de hilos (transacciones concurrentes)", fontsize=11)
axes[1].set_ylabel("Latencia promedio por transacción (ms)", fontsize=11)
axes[1].grid(True, alpha=0.3)

# Añadir valores en los puntos (en ms)
for i, row in data.iterrows():
    axes[1].annotate(f'{row["latencia_ms"]:.2f}ms', 
                    xy=(row['threads'], row['latencia_ms']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

# Añadir línea de referencia de latencia consistente
media_latencia = data['latencia_ms'].mean()
axes[1].axhline(y=media_latencia, color='red', linestyle='--', linewidth=2, 
                label=f'Latencia promedio global: {media_latencia:.2f}ms', alpha=0.7)
axes[1].legend(fontsize=10)

plt.tight_layout()
plt.show()
