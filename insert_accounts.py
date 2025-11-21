import mysql.connector

POOL_CONFIG = {
    'host': 'gateway01.us-east-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '4SUir1NzoHpaiZR.root',
    'password': 'drE83TL7cJpCSrRE',
    'database': 'bank'
}

conn = mysql.connector.connect(**POOL_CONFIG)
cur = conn.cursor()

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
