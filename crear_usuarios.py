from werkzeug.security import generate_password_hash
from db import obtener_conexion


def crear_usuario(usuario, password, rol):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    password_hash = generate_password_hash(password)

    sql = """
        INSERT INTO usuarios (usuario, password_hash, rol)
        VALUES (%s, %s, %s)
    """

    cursor.execute(sql, (usuario, password_hash, rol))
    conexion.commit()

    cursor.close()
    conexion.close()

    print(f"Usuario creado: {usuario} - Rol: {rol}")


crear_usuario("admin", "admin123", "admin")
crear_usuario("profe1", "1234", "profesor")