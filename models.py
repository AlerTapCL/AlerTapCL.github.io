from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime  # Importación necesaria

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(20), unique=True)

    # Campos de ficha médica
    edad = db.Column(db.String(10))
    grupo_sanguineo = db.Column(db.String(10))
    enfermedades = db.Column(db.String(200))
    medicamentos = db.Column(db.String(200))
    alergias = db.Column(db.String(200))
    contacto_emergencia = db.Column(db.String(100))
    telefono = db.Column(db.String(30))
    observaciones = db.Column(db.String(300))
    foto_url = db.Column(db.String(300))

    # ✅ Campo para notificaciones
    correo_notificacion = db.Column(db.String(120))

    # ✅ Verificación de correo
    verificado = db.Column(db.Boolean, default=False)
    codigo_verificacion = db.Column(db.String(6), nullable=True)
    expiracion_codigo = db.Column(db.DateTime, nullable=True)
