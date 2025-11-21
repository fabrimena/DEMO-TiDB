import time
import random
import csv
import threading
import logging
from mysql.connector.pooling import MySQLConnectionPool
import mysql.connector

# Silenciar logs de mysql.connector
logging.getLogger("mysql.connector").setLevel(logging.WARNING)

# CONFIGURAR esto con sus valores
POOL_CONFIG = {
    'pool_name': 'tidb_pool',
    'pool_size': 32, 
    'host': 'gateway01.us-east-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '4SUir1NzoHpaiZR.root',
    'password': 'drE83TL7cJpCSrRE',
    'database': 'bank'
}

pool = MySQLConnectionPool(**POOL_CONFIG)

def get_connection_with_wait(max_wait=5):
    start = time.time()
    while True:
        try:
            return pool.get_connection()
        except mysql.connector.errors.PoolError:
            if time.time() - start > max_wait:
                raise
            time.sleep(0.001)  # esperar 1ms antes de intentar de nuevo

def single_transfer_with_retries(tx_id=None, max_retries=3):
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        conn = None
        cur = None
        start = time.time()  # Inicializar start antes de cualquier operación
        try:
            conn = get_connection_with_wait()
            conn.autocommit = False  # Deshabilitar autocommit explícitamente
            cur = conn.cursor()
            # Seleccionar 2 cuentas aleatorias del total de 100
            from_id, to_id = random.sample(range(1, 101), 2)
            amount = random.randint(10,200)
            
            # No usar START TRANSACTION explícito - la transacción inicia automáticamente
            cur.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s;", (amount, from_id))
            cur.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s;", (amount, to_id))
            conn.commit()
            elapsed = time.time() - start
            cur.close()
            conn.close()
            return True, elapsed
            
        except (TimeoutError, mysql.connector.errors.PoolError):
            # Errores de pool - reintentar sin espera
            if cur:
                try:
                    cur.close()
                except Exception:  # pylint: disable=broad-except
                    pass
            if conn:
                try:
                    conn.close()
                except Exception:  # pylint: disable=broad-except
                    pass
            if attempt < max_retries:
                continue
            return False, None

        except mysql.connector.Error as e:
            # Cerrar cursor ANTES de rollback para evitar estado inválido
            if cur:
                try:
                    cur.close()
                except Exception:  # pylint: disable=broad-except
                    pass
            # Ahora hacer rollback con cursor ya cerrado
            if conn:
                try:
                    conn.rollback()
                except Exception:  # pylint: disable=broad-except
                    pass
                try:
                    conn.close()
                except Exception:  # pylint: disable=broad-except
                    pass
            
            # Deadlock errno: 1213 (MySQL/TiDB) - reintentar sin espera adicional
            if hasattr(e, 'errno') and e.errno == 1213 and attempt < max_retries:
                continue
            else:
                # error no esperado o último intento -> fallo
                return False, time.time() - start

        except Exception:  # pylint: disable=broad-except
            # Capturar cualquier otra excepción - hacer rollback también
            if cur:
                try:
                    cur.close()
                except Exception:  # pylint: disable=broad-except
                    pass
            if conn:
                try:
                    conn.rollback()
                except Exception:  # pylint: disable=broad-except
                    pass
                try:
                    conn.close()
                except Exception:  # pylint: disable=broad-except
                    pass
            if attempt < max_retries:
                continue
            return False, None
    
    return False, None

def run_benchmark(n_threads):
    latencies = []
    success_count = 0
    failed_transactions = []
    threads = []
    lock = threading.Lock()

    def worker(i):
        nonlocal success_count
        ok, latency = single_transfer_with_retries(i)
        with lock:
            if ok:
                success_count += 1
                latencies.append(latency)
            else:
                # Agregar a cola de reagendamiento
                failed_transactions.append(i)

    start = time.time()
    
    # FASE 1: Ejecutar todas las transacciones iniciales
    for i in range(n_threads):
        t = threading.Thread(target=worker, args=(i,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    
    initial_failed = len(failed_transactions)
    phase = 1
    
    # FASE 2+: Reagendar transacciones fallidas hasta que no haya más fallos
    while failed_transactions:
        phase += 1
        threads = []
        reagendadas = failed_transactions.copy()
        failed_transactions = []
        
        for tx_id in reagendadas:
            t = threading.Thread(target=worker, args=(tx_id,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    
    elapsed_total = time.time() - start
    mean_lat = sum(latencies)/len(latencies) if latencies else None
    
    return {
        'threads': n_threads,
        'time_seconds': elapsed_total,
        'successful': success_count,
        'mean_latency_success_s': mean_lat,
        'initial_failed': initial_failed,
        'phases': phase
    }

if __name__ == "__main__":
    niveles = [10,20,50,100]
    resultados = []
    for n in niveles:
        print(f"Ejecutando {n} hilos ...")
        r = run_benchmark(n)
        print(r)
        resultados.append(r)
        time.sleep(3)

    # Guardar CSV
    keys = ['threads','time_seconds','successful','mean_latency_success_s','initial_failed','phases']
    with open('benchmark_results.csv','w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in resultados:
            writer.writerow(r)
    print("Resultados guardados en benchmark_results.csv")
