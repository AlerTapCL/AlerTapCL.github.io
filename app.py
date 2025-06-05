from flask import Flask, render_template, request, redirect, url_for, flash, abort
import json
import smtplib
import uuid
from email.message import EmailMessage
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, Usuario

app = Flask(__name__)
app.secret_key = 'clave_secreta_flash'

# Configuración base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
db.init_app(app)
bcrypt = Bcrypt(app)

# Login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Cargar personas desde JSON
with open("personas.json", "r", encoding="utf-8") as f:
    personas = json.load(f)

# === Rutas ===
@app.route('/')
def inicio():
    return render_template("inicio.html")

@app.route('/<perfil>')
def mostrar_perfil(perfil):
    persona = personas.get(perfil)
    if persona and persona.get("activo", True):
        return render_template("perfil.html", persona=persona)
    else:
        abort(404)

@app.route('/como-funciona')
def como_funciona():
    return render_template("como_funciona.html")

@app.route('/perfil-ejemplo')
def perfil_ejemplo():
    return render_template("perfil_ejemplo.html")

@app.route('/faq')
def faq():
    return render_template("faq.html")

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        mensaje = request.form.get('mensaje')
        enviar_correo(nombre, mensaje)
        flash("Tu mensaje fue enviado correctamente.")
        return redirect(url_for('mensaje_enviado'))
    return render_template("contacto.html")

@app.route('/mensaje-enviado')
def mensaje_enviado():
    return render_template("mensaje_enviado.html")

# === Registro de usuario ===
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        existente = Usuario.query.filter_by(correo=correo).first()
        if existente:
            flash("Ese correo ya está registrado.")
            return redirect(url_for('registro'))

        slug_unico = uuid.uuid4().hex[:10]
        hash_pass = bcrypt.generate_password_hash(contraseña).decode('utf-8')

        nuevo = Usuario(
            nombre=nombre,
            correo=correo,
            contraseña=hash_pass,
            slug=slug_unico,
            correo_notificacion=correo  # Por defecto usamos el mismo correo para notificaciones
        )
        db.session.add(nuevo)
        db.session.commit()

        flash("¡Registro exitoso! Ya puedes iniciar sesión.")
        return redirect(url_for('login'))

    return render_template("registro.html")

# === Login ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and bcrypt.check_password_hash(usuario.contraseña, contraseña):
            login_user(usuario)
            flash("Sesión iniciada correctamente.")
            return redirect(url_for('mi_perfil'))
        else:
            flash("Correo o contraseña incorrectos.")
            return redirect(url_for('login'))

    return render_template("login.html")

# === Logout ===
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión.")
    return redirect(url_for('inicio'))

# === Perfil privado ===
@app.route('/mi-perfil')
@login_required
def mi_perfil():
    return render_template("mi_perfil.html", usuario=current_user)

# === Editar perfil ===
@app.route('/mi-perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    if request.method == 'POST':
        current_user.nombre = request.form.get('nombre')
        current_user.edad = request.form.get('edad')
        current_user.grupo_sanguineo = request.form.get('grupo_sanguineo')
        current_user.enfermedades = request.form.get('enfermedades')
        current_user.medicamentos = request.form.get('medicamentos')
        current_user.alergias = request.form.get('alergias')
        current_user.contacto_emergencia = request.form.get('contacto_emergencia')
        current_user.telefono = request.form.get('telefono')
        current_user.observaciones = request.form.get('observaciones')
        current_user.foto_url = request.form.get('foto_url')
        current_user.correo_notificacion = request.form.get('correo_notificacion') or current_user.correo

        nueva_contraseña = request.form.get('contraseña')
        if nueva_contraseña and nueva_contraseña.strip():
            current_user.contraseña = bcrypt.generate_password_hash(nueva_contraseña).decode('utf-8')

        db.session.commit()
        flash("Perfil actualizado correctamente.")
        return redirect(url_for('mi_perfil'))

    return render_template("editar_perfil.html", usuario=current_user)

# === Perfil público ===
@app.route('/perfil/<slug>')
def perfil_publico(slug):
    usuario = Usuario.query.filter_by(slug=slug).first_or_404()

    # Notificar al dueño del perfil por correo
    if usuario.correo:
        enviar_aviso_acceso(usuario)

    return render_template("perfil_publico.html", usuario=usuario)

# === Envío de correo general ===
def enviar_correo(nombre, mensaje):
    remitente = "alertapteam@gmail.com"
    destinatario = "alertapteam@gmail.com"
    clave_app = "makjbbeigmvofxlo"

    msg = EmailMessage()
    msg['Subject'] = "Nuevo mensaje desde AlerTap"
    msg['From'] = remitente
    msg['To'] = destinatario
    msg.set_content(f"Nombre: {nombre}\n\nMensaje:\n{mensaje}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, clave_app)
            smtp.send_message(msg)
            print("✅ Correo enviado con éxito.")
    except Exception as e:
        print("❌ Error al enviar el correo:", e)

# === Aviso de acceso al perfil ===
def enviar_aviso_acceso(usuario):
    remitente = "alertapteam@gmail.com"
    destinatario = usuario.correo_notificacion or usuario.correo
    clave_app = "makjbbeigmvofxlo"

    msg = EmailMessage()
    msg['Subject'] = "⚠️ Se accedió a tu ficha médica AlerTap"
    msg['From'] = remitente
    msg['To'] = destinatario
    msg.set_content(f"""
Hola {usuario.nombre},

Alguien accedió a tu ficha médica digital en AlerTap usando tu enlace personalizado:
https://alertap.cl/perfil/{usuario.slug}

Si tú no lo escaneaste, revisa tu entorno y considera tomar precauciones.

— Equipo AlerTap
""")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, clave_app)
            smtp.send_message(msg)
            print(f"✅ Aviso enviado a {destinatario}")
    except Exception as e:
        print("❌ Error al enviar aviso:", e)

# === Error 404 ===
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("404.html"), 404

@app.route('/testimonios')
def testimonios():
    return render_template("testimonios.html")


# === Iniciar app ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

