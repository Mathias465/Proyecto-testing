import mysql.connector


def obtener_conexion():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",  # coloca aquí tu contraseña de MySQL
        database="sistema_notas_db"
    )