import pytest
import app as sistema

# FIXTURES

@pytest.fixture
def client():
    sistema.app.config["TESTING"] = True

    with sistema.app.test_client() as client:
        yield client

# HELPERS

def fake_user():
    return {
        "id": 1,
        "usuario": "profe1",
        "password_hash": "hash",
        "rol": "profesor",
        "activo": True
    }


def login_session(client):
    with client.session_transaction() as sess:
        sess["usuario_id"] = 1
        sess["usuario"] = "profe1"
        sess["rol"] = "profesor"


# CP01 - Login correcto
def test_login_correcto_redirige_a_menu(client, monkeypatch):

    class FakeCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchone(self):
            return fake_user()

        def close(self):
            pass

    class FakeConexion:
        def cursor(self, dictionary=True):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        sistema,
        "obtener_conexion",
        lambda: FakeConexion()
    )

    monkeypatch.setattr(
        sistema,
        "check_password_hash",
        lambda hash, password: True
    )

    response = client.post("/", data={
        "usuario": "profe1",
        "password": "1234"
    })

    assert response.status_code == 302
    assert "/menu" in response.headers["Location"]


# CP02 - Login incorrecto
def test_login_incorrecto(client, monkeypatch):

    class FakeCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchone(self):
            return None

        def close(self):
            pass

    class FakeConexion:
        def cursor(self, dictionary=True):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        sistema,
        "obtener_conexion",
        lambda: FakeConexion()
    )

    response = client.post("/", data={
        "usuario": "x",
        "password": "x"
    })

    assert response.status_code == 200
    assert "Credenciales incorrectas" in response.data.decode()



# CP03 - Menú sin login
def test_menu_sin_login(client):
    response = client.get("/menu")

    assert response.status_code == 302

# CP04 - Promedio sin notas
def test_calcular_promedio_sin_notas(monkeypatch):

    class FakeCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return []

        def close(self):
            pass

    class FakeConexion:
        def cursor(self, dictionary=True):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        sistema,
        "obtener_conexion",
        lambda: FakeConexion()
    )

    promedio = sistema.calcular_promedio("1")

    assert promedio == 0


# CP05 - Promedio normal
def test_calcular_promedio_con_notas(monkeypatch):

    class FakeCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return [
                {"valor": 12, "es_nsp": False},
                {"valor": 16, "es_nsp": False},
                {"valor": 14, "es_nsp": False}
            ]

        def close(self):
            pass

    class FakeConexion:
        def cursor(self, dictionary=True):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        sistema,
        "obtener_conexion",
        lambda: FakeConexion()
    )

    promedio = sistema.calcular_promedio("1")

    assert promedio == 14


# CP06 - Promedio con NSP
def test_calcular_promedio_con_nsp(monkeypatch):

    class FakeCursor:
        def execute(self, *args, **kwargs):
            pass

        def fetchall(self):
            return [
                {"valor": 15, "es_nsp": False},
                {"valor": None, "es_nsp": True}
            ]

        def close(self):
            pass

    class FakeConexion:
        def cursor(self, dictionary=True):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        sistema,
        "obtener_conexion",
        lambda: FakeConexion()
    )

    promedio = sistema.calcular_promedio("1")

    assert promedio == 7.5


# CP07 - Registrar nota válida
def test_registrar_nota_valida(client, monkeypatch):

    login_session(client)

    monkeypatch.setattr(
        sistema,
        "estado_plazo",
        lambda: "activo"
    )

    class FakeCursor:

        def execute(self, sql, params=None):

            if "SELECT codigo FROM estudiantes" in sql:
                self.result = {"codigo": "1"}

            elif "COUNT(*)" in sql:
                self.result = {"total": 0}

        def fetchone(self):
            return self.result

        def close(self):
            pass

    class FakeConexion:

        def cursor(self, dictionary=True):
            return FakeCursor()

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(
        sistema,
        "obtener_conexion",
        lambda: FakeConexion()
    )

    response = client.post("/registrar", data={
        "codigo": "1",
        "nota": "18"
    })

    assert response.status_code == 302


# CP08 - Nota fuera de rango
def test_registrar_fuera_rango(client, monkeypatch):

    login_session(client)

    monkeypatch.setattr(
        sistema,
        "estado_plazo",
        lambda: "activo"
    )

    class FakeCursor:

        def execute(self, sql, params=None):

            if "SELECT codigo FROM estudiantes" in sql:
                self.result = {"codigo": "1"}

            elif "COUNT(*)" in sql:
                self.result = {"total": 0}

        def fetchone(self):
            return self.result

        def close(self):
            pass

    class FakeConexion:

        def cursor(self, dictionary=True):
            return FakeCursor()

        def close(self):
            pass

    monkeypatch.setattr(
        sistema,
        "obtener_conexion",
        lambda: FakeConexion()
    )

    response = client.post("/registrar", data={
        "codigo": "1",
        "nota": "25"
    })

    assert response.status_code == 302


# CP09 - Logout
def test_logout(client):

    login_session(client)

    response = client.get("/logout")

    assert response.status_code == 302
    assert "/" in response.headers["Location"]