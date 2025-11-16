import mysql.connector

POOL_CONFIG = {
    'host': 'tu-HOST',
    'port': 4000,
    'user': 'tu-USERNAME',
    'password': 'tu-PASSWORD',
    'database': 'bank'
}

conn = mysql.connector.connect(**POOL_CONFIG)
cur = conn.cursor()

# Insertar las 3 cuentas originales
cur.execute("""
    INSERT INTO accounts (name, balance) VALUES
    ('Alice', 1000.00),
    ('Bob', 500.00),
    ('Carol', 2000.00)
""")

# Insertar 97 cuentas adicionales
additional_accounts = [(f'User_{i}', 1000.00 + i*10) for i in range(1, 98)]
cur.executemany(
    "INSERT INTO accounts (name, balance) VALUES (%s, %s)",
    additional_accounts
)

conn.commit()
cur.close()
conn.close()

print("Se han insertado exitosamente 100 cuentas en total (3 + 97)")
