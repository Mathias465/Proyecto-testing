DROP DATABASE sistema_notas_db;
CREATE DATABASE IF NOT EXISTS sistema_notas_db;
USE sistema_notas_db;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('admin', 'profesor') NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE estudiantes (
    codigo VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_codigo VARCHAR(20) NOT NULL,
    valor DECIMAL(5,2) NULL,
    es_nsp BOOLEAN DEFAULT FALSE,
    profesor_id INT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (estudiante_codigo) REFERENCES estudiantes(codigo)
        ON DELETE CASCADE,

    FOREIGN KEY (profesor_id) REFERENCES usuarios(id)
        ON DELETE RESTRICT
);