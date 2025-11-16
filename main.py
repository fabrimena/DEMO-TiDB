import mysql.connector
import threading
import random
import time

config = {
    'host': 'tu-HOST',
    'port': 4000,
    'user': 'tu-USERNAME',
    'password': 'tu-PASSWORD',
    'database': 'bank'
}

def transfer(id_transaccion):
    conn = mysql.connector.connect(**config)
    cur = conn.cursor()
    from_id, to_id = random.sample([1, 2, 3], 2)
    amount = random.randint(10, 200)

    try:
        cur.execute("START TRANSACTION;")
        cur.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s;", (amount, from_id))
        cur.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s;", (amount, to_id))
        conn.commit()
        print(f"Transaccion Exitosa {id_transaccion}: {amount} de {from_id} → {to_id}")
    except Exception as e:
        conn.rollback()
        print(f"Error en transaccion {id_transaccion}: {e}")
    finally:
        cur.close()
        conn.close()

# Ejecutar 20 transacciones en paralelo
threads = []
start = time.time()
for i in range(20):
    t = threading.Thread(target=transfer, args=(i,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

end = time.time()
print(f"\n Tiempo total: {end - start:.2f} segundos")

# Verificar consistencia
conn = mysql.connector.connect(**config)
cur = conn.cursor()
cur.execute("SELECT id, name, balance FROM accounts;")
print("\nEstado final de las cuentas:")
for row in cur.fetchall():
    print(row)
cur.execute("SELECT SUM(balance) FROM accounts;")
total = cur.fetchone()[0]
print(f"\n Suma total de dinero: {total}")
cur.close()
conn.close()
