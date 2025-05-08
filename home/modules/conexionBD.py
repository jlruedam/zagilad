import pyodbc

from decouple import config


def conexionBD(query):
    
    # Configurar la conexión
    server = config('SERVER_LAKE')  
    username = config('USERNAME_SERVER_LAKE')   
    password = config('PASSWORD_SERVER_LAKE')     

    # Crear la conexión
    conn = pyodbc.connect(
        f"DRIVER={{SQL Server}};SERVER={server};UID={username};PWD={password}"
    )

    cursor = conn.cursor()

    complex_qr_pr_ate = query

    # Ejecutar una consulta
    cursor.execute(complex_qr_pr_ate)

    # Obtener los resultados
    rows = cursor.fetchall()
    
    # Cerrar conexión
    conn.close()
    
    rows = [list(row) for row in rows]

    return rows



