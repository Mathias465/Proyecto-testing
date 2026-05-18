from flask import Flask, render_template, request, redirect, session, url_for, flash
from datetime import datetime
from werkzeug.security import check_password_hash
from db import obtener_conexion
import mysql.connector

app = Flask(__name__)
app.secret_key = "clave_secreta"

# -------- CONFIGURACIÓN --------
FECHA_INICIO = datetime(2026, 4, 1)
FECHA_FIN = datetime(2026, 6, 30)
MAX_NOTAS = 3

usuarios = {
    "profe1": "1234",
    "admin": "admin"
}

estudiantes = {
    "1": {"nombre": "Leonardo Leonesco", "notas": []},
    "2": {"nombre": "Adrian SantaCruz", "notas": []}
}

# -------- FUNCIONES --------

def usuario_logueado():
    return "usuario_id" in session


def es_admin():
    return session.get("rol") == "admin"


def es_profesor():
    return session.get("rol") == "profesor"


def estado_plazo():
    ahora = datetime.now()

    if ahora < FECHA_INICIO:
        return "no_iniciado"
    elif FECHA_INICIO <= ahora <= FECHA_FIN:
        return "activo"
    else:
        return "finalizado"


def calcular_promedio(codigo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT valor, es_nsp
        FROM notas
        WHERE estudiante_codigo = %s
    """, (codigo,))

    notas = cursor.fetchall()

    cursor.close()
    conexion.close()

    if len(notas) == 0:
        return 0

    suma = 0

    for nota in notas:
        if nota["es_nsp"]:
            suma += 0
        else:
            suma += float(nota["valor"])

    return suma / len(notas)


# -------- RUTAS --------

@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        password = request.form["password"].strip()

        conexion = obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        sql = """
            SELECT id, usuario, password_hash, rol, activo
            FROM usuarios
            WHERE usuario = %s
        """

        cursor.execute(sql, (usuario,))
        user = cursor.fetchone()

        cursor.close()
        conexion.close()

        if user and user["activo"] and check_password_hash(user["password_hash"], password):
            session["usuario_id"] = user["id"]
            session["usuario"] = user["usuario"]
            session["rol"] = user["rol"]

            flash("Inicio de sesión correcto.", "success")
            return redirect(url_for("menu"))

        error = "Credenciales incorrectas"

    return render_template("login.html", error=error)


@app.route("/menu")
def menu():
    if not usuario_logueado():
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            e.codigo,
            e.nombre,
            COUNT(n.id) AS total_notas
        FROM estudiantes e
        LEFT JOIN notas n ON n.estudiante_codigo = e.codigo
        GROUP BY e.codigo, e.nombre
        ORDER BY e.codigo
    """)

    estudiantes = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "menu.html",
        estudiantes=estudiantes,
        rol=session.get("rol"),
        usuario=session.get("usuario"),
        fecha_inicio=FECHA_INICIO,
        fecha_fin=FECHA_FIN,
        estado=estado_plazo()
    )

@app.route("/registrar_alumno", methods=["POST"])
def registrar_alumno():
    if not usuario_logueado():
        return redirect(url_for("login"))

    if not es_admin():
        flash("No tienes permisos para registrar alumnos.", "error")
        return redirect(url_for("menu"))

    codigo = request.form["codigo"].strip()
    nombre = request.form["nombre"].strip()

    if codigo == "" or nombre == "":
        flash("Debe ingresar código y nombre del alumno.", "warning")
        return redirect(url_for("menu"))

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        sql = """
            INSERT INTO estudiantes (codigo, nombre)
            VALUES (%s, %s)
        """
        cursor.execute(sql, (codigo, nombre))
        conexion.commit()

        flash("Alumno registrado correctamente.", "success")

    except mysql.connector.Error:
        flash("El código del alumno ya existe o hubo un error al registrar.", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("menu"))


@app.route("/registrar", methods=["POST"])
def registrar_nota():
    if not usuario_logueado():
        return redirect(url_for("login"))

    if not es_profesor():
        flash("Solo los profesores pueden registrar notas.", "error")
        return redirect(url_for("menu"))

    if estado_plazo() != "activo":
        flash("Fuera del periodo de registro.", "warning")
        return redirect(url_for("menu"))

    codigo = request.form["codigo"].strip()
    nota = request.form["nota"].strip().upper()

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT codigo FROM estudiantes WHERE codigo = %s", (codigo,))
    estudiante = cursor.fetchone()

    if not estudiante:
        cursor.close()
        conexion.close()
        flash("El ID ingresado no pertenece a ningún alumno registrado.", "error")
        return redirect(url_for("menu"))

    cursor.execute(
        "SELECT COUNT(*) AS total FROM notas WHERE estudiante_codigo = %s",
        (codigo,)
    )
    total_notas = cursor.fetchone()["total"]

    if total_notas >= MAX_NOTAS:
        cursor.close()
        conexion.close()
        flash("Este alumno ya tiene el máximo de 3 notas registradas.", "warning")
        return redirect(url_for("menu"))

    if nota == "":
        cursor.close()
        conexion.close()
        flash("Debe ingresar una nota o NSP.", "warning")
        return redirect(url_for("menu"))

    if nota == "NSP":
        sql = """
            INSERT INTO notas (estudiante_codigo, valor, es_nsp, profesor_id)
            VALUES (%s, NULL, TRUE, %s)
        """
        cursor.execute(sql, (codigo, session["usuario_id"]))
        conexion.commit()

        cursor.close()
        conexion.close()

        flash("NSP registrado correctamente.", "success")
        return redirect(url_for("menu"))

    try:
        nota_float = float(nota)

        if nota_float < 0 or nota_float > 20:
            cursor.close()
            conexion.close()
            flash("La nota debe estar entre 0 y 20.", "error")
            return redirect(url_for("menu"))

        sql = """
            INSERT INTO notas (estudiante_codigo, valor, es_nsp, profesor_id)
            VALUES (%s, %s, FALSE, %s)
        """
        cursor.execute(sql, (codigo, nota_float, session["usuario_id"]))
        conexion.commit()

        flash("Nota registrada correctamente.", "success")

    except ValueError:
        flash("Ingrese una nota válida: número entre 0 y 20 o NSP.", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("menu"))


@app.route("/historial/<codigo>")
def historial(codigo):
    if not usuario_logueado():
        return redirect(url_for("login"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute(
        "SELECT codigo, nombre FROM estudiantes WHERE codigo = %s",
        (codigo,)
    )
    estudiante = cursor.fetchone()

    if not estudiante:
        cursor.close()
        conexion.close()
        flash("Alumno no encontrado.", "error")
        return redirect(url_for("menu"))

    cursor.execute("""
        SELECT id, valor, es_nsp, creado_en, actualizado_en
        FROM notas
        WHERE estudiante_codigo = %s
        ORDER BY id
    """, (codigo,))

    notas = cursor.fetchall()

    cursor.close()
    conexion.close()

    estudiante["notas"] = notas

    promedio = calcular_promedio(codigo)
    total_notas = len(notas)
    total_nsp = sum(1 for nota in notas if nota["es_nsp"])

    if total_notas == 3 and total_nsp == 3:
        estado = "NSP"
    elif promedio >= 11:
        estado = "Aprobado"
    else:
        estado = "Desaprobado"

    return render_template(
        "historial.html",
        estudiante=estudiante,
        codigo=codigo,
        promedio=round(promedio, 2),
        estado=estado,
        rol=session.get("rol")
    )


@app.route("/editar/<int:nota_id>", methods=["GET", "POST"])
def editar_nota(nota_id):
    if not usuario_logueado():
        return redirect(url_for("login"))

    if not es_profesor():
        flash("Solo los profesores pueden modificar notas.", "error")
        return redirect(url_for("menu"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT n.id, n.estudiante_codigo, n.valor, n.es_nsp, e.nombre
        FROM notas n
        INNER JOIN estudiantes e ON e.codigo = n.estudiante_codigo
        WHERE n.id = %s
    """, (nota_id,))

    nota_actual = cursor.fetchone()

    if not nota_actual:
        cursor.close()
        conexion.close()
        flash("Nota no encontrada.", "error")
        return redirect(url_for("menu"))

    if request.method == "POST":
        nueva_nota = request.form["nota"].strip().upper()

        if nueva_nota == "NSP":
            cursor.execute("""
                UPDATE notas
                SET valor = NULL, es_nsp = TRUE
                WHERE id = %s
            """, (nota_id,))
            conexion.commit()

            cursor.close()
            conexion.close()

            flash("Nota actualizada correctamente.", "success")
            return redirect(url_for("historial", codigo=nota_actual["estudiante_codigo"]))

        try:
            nueva_nota_float = float(nueva_nota)

            if nueva_nota_float < 0 or nueva_nota_float > 20:
                flash("La nota debe estar entre 0 y 20.", "error")
            else:
                cursor.execute("""
                    UPDATE notas
                    SET valor = %s, es_nsp = FALSE
                    WHERE id = %s
                """, (nueva_nota_float, nota_id))

                conexion.commit()
                flash("Nota actualizada correctamente.", "success")

                cursor.close()
                conexion.close()

                return redirect(url_for("historial", codigo=nota_actual["estudiante_codigo"]))

        except ValueError:
            flash("Ingrese una nota válida: número entre 0 y 20 o NSP.", "error")

    cursor.close()
    conexion.close()

    return render_template("editar.html", nota=nota_actual)


@app.route("/eliminar/<int:nota_id>")
def eliminar_nota(nota_id):
    if not usuario_logueado():
        return redirect(url_for("login"))

    if not es_profesor():
        flash("Solo los profesores pueden eliminar notas.", "error")
        return redirect(url_for("menu"))

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, estudiante_codigo
        FROM notas
        WHERE id = %s
    """, (nota_id,))

    nota = cursor.fetchone()

    if not nota:
        cursor.close()
        conexion.close()
        flash("La nota no existe o ya fue eliminada.", "error")
        return redirect(url_for("menu"))

    codigo = nota["estudiante_codigo"]

    cursor.execute("""
        DELETE FROM notas
        WHERE id = %s
    """, (nota_id,))

    conexion.commit()

    cursor.close()
    conexion.close()

    flash("Nota eliminada correctamente.", "success")
    return redirect(url_for("historial", codigo=codigo))


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login"))


# -------- RUN --------

if __name__ == "__main__":
    app.run(debug=True)