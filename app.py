import os
import zipfile
import io
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, after_this_request, Blueprint
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, static_url_path='/firmasclientes/static', static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = '/var/www/firmasclientes/uploads'
app.config['OUTPUT_FOLDER'] = '/var/www/firmasclientes/output'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Configuración del logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/error.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

# Coordenadas proporcionadas
adjusted_coordinates_provided = {
    'WEEK FROM': (149, 489),
    'TO': (245, 489),
    'CASE #/CLIENTS NAME': (217, 539),
    'MONDAY': (433, 190),
    'TUESDAY': (433, 240),
    'WEDNESDAY': (433, 290),
    'THURSDAY': (433, 340),
    'FRIDAY': (433, 390),
    'MONDAY TIME': (433, 175),
    'TUESDAY TIME': (433, 225),
    'WEDNESDAY TIME': (433, 275),
    'THURSDAY TIME': (433, 325),
    'FRIDAY TIME': (433, 375)
}

def check_environment():
    app.logger.info("Realizando diagnóstico del entorno")
    app.logger.info(f"Contenido de UPLOAD_FOLDER: {os.listdir(app.config['UPLOAD_FOLDER'])}")
    app.logger.info(f"Contenido de OUTPUT_FOLDER: {os.listdir(app.config['OUTPUT_FOLDER'])}")

def create_weekly_pdfs_from_csv(csv_path, template_pdf_path, main_output_dir, start_dates, time_period):
    try:
        app.logger.info(f"Iniciando la creación de PDFs semanales desde el CSV para las fechas: {start_dates}")
        if time_period == 'morning':
            times = ['08:00 AM / 12:15 PM'] * 5
        elif time_period == 'afternoon':
            times = ['12:45 PM / 05:00 PM'] * 5

        df = pd.read_csv(csv_path)
        app.logger.info(f"CSV leído correctamente: {csv_path}")

        for start_date in start_dates:
            week_from = pd.to_datetime(start_date)
            app.logger.info(f"Generando PDFs para la semana comenzando el {week_from}")

            if not os.path.exists(main_output_dir):
                os.makedirs(main_output_dir)

            week_output_dir = os.path.join(main_output_dir, f"Week_{week_from.strftime('%Y-%m-%d')}")
            if not os.path.exists(week_output_dir):
                os.makedirs(week_output_dir)

            dates = [(week_from + pd.DateOffset(days=i)).strftime('%m/%d/%Y') for i in range(5)]

            for index, row in df.iterrows():
                client_name = row["CLIENT'S NAME"]
                client_id = row["CASE #"]

                if pd.isnull(client_name) or client_name.strip() == "":
                    continue

                combined_name_id = f"{client_id} {client_name}"

                data = {
                    'WEEK FROM': week_from.strftime('%m/%d/%Y'),
                    'TO': (week_from + pd.DateOffset(days=4)).strftime('%m/%d/%Y'),
                    'CASE #/CLIENTS NAME': combined_name_id,
                    'DATES': dates[::-1],
                    'TIMES': times
                }

                safe_client_name = "".join([c for c in combined_name_id if c.isalnum() or c in (' ', '_')]).rstrip()
                output_path = os.path.join(week_output_dir, f"{safe_client_name}_Week_{week_from.strftime('%m-%d-%Y')}.pdf")

                fill_pdf(template_pdf_path, output_path, data)
                app.logger.info(f"PDF creado: {output_path}")
    except Exception as e:
        app.logger.error(f"Error creando PDFs: {e}", exc_info=True)
        raise

def fill_pdf(template_path, output_path, data):
    try:
        app.logger.info(f"Llenando PDF para {data['CASE #/CLIENTS NAME']}")
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        field_coordinates = adjusted_coordinates_provided

        can.drawString(*field_coordinates['WEEK FROM'], data['WEEK FROM'])
        can.drawString(*field_coordinates['TO'], data['TO'])
        can.drawString(*field_coordinates['CASE #/CLIENTS NAME'], data['CASE #/CLIENTS NAME'])

        for day, date, time, day_field, time_field in zip(
            ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'],
            data['DATES'],
            data['TIMES'],
            ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'],
            ['MONDAY TIME', 'TUESDAY TIME', 'WEDNESDAY TIME', 'THURSDAY TIME', 'FRIDAY TIME']
        ):
            can.drawString(*field_coordinates[day_field], date)
            can.drawString(*field_coordinates[time_field], time)

        can.save()
        packet.seek(0)

        existing_pdf = PdfReader(template_path)
        new_pdf = PdfReader(packet)
        output = PdfWriter()

        page = existing_pdf.pages[0]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)

        with open(output_path, "wb") as outputStream:
            output.write(outputStream)
    except Exception as e:
        app.logger.error(f"Error llenando PDF: {e}", exc_info=True)
        raise

def generate_weekly_dates(start_date, end_date):
    try:
        app.logger.info(f"Generando fechas semanales desde {start_date} hasta {end_date}")
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        app.logger.info(f"Fechas convertidas: start_date={start_date}, end_date={end_date}")
        
        week_dates = []
        current_date = start_date
        while current_date <= end_date:
            week_dates.append(current_date.strftime('%Y-%m-%d'))
            app.logger.info(f"Fecha añadida: {current_date.strftime('%Y-%m-%d')}")
            current_date += pd.DateOffset(weeks=1)
            app.logger.info(f"Próxima fecha a considerar: {current_date}")

        app.logger.info(f"Fechas generadas: {week_dates}")
        return week_dates
    except Exception as e:
        app.logger.error(f"Error generando fechas semanales: {e}", exc_info=True)
        return []

def create_zip(zip_filename, directories):
    try:
        app.logger.info(f"Creando archivo ZIP en: {zip_filename}")
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for directory in directories:
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        app.logger.info(f"Añadiendo {file_path} al archivo ZIP")
                        zipf.write(file_path, os.path.relpath(file_path, start=os.path.dirname(directory)))
        
        if not os.path.exists(zip_filename):
            raise FileNotFoundError(f"El archivo ZIP no se creó: {zip_filename}")
        
        app.logger.info(f"Archivo ZIP creado correctamente: {zip_filename}")

        # Verificar el contenido del archivo ZIP
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            zip_contents = zipf.namelist()
            app.logger.info(f"Contenido del archivo ZIP: {zip_contents}")

    except Exception as e:
        app.logger.error(f"Error creando el archivo ZIP: {e}", exc_info=True)
        raise

bp = Blueprint('firmasclientes', __name__, url_prefix='/firmasclientes')
@bp.route('/', methods=['GET', 'POST'])
def upload_file():
    check_environment()  # Ejecutar diagnóstico antes de cada solicitud
    file_path = None
    try:
        if request.method == 'POST':
            app.logger.info("Recepción de archivo CSV iniciado")
            file = request.files['csv_file']
            time_period = request.form['time_period']
            date_option = request.form['date_option']

            app.logger.info(f"Opción de fecha seleccionada: {date_option}")
            app.logger.info(f"Periodo de tiempo seleccionado: {time_period}")

            start_dates = []
            if date_option == 'specific_dates':
                app.logger.info("Procesando fechas específicas")
                specific_dates = request.form.getlist('specific_dates[]')
                start_dates = [date.strip() for date in specific_dates if date.strip()]
            elif date_option == 'range':
                app.logger.info("Procesando rango de fechas")
                start_date = request.form.get('start_date')
                end_date = request.form.get('end_date')
                app.logger.info(f"Fechas de rango recibidas: inicio={start_date}, fin={end_date}")
                if not start_date or not end_date:
                    app.logger.error("Faltan las fechas de inicio o fin para el rango de fechas")
                    return "Faltan las fechas de inicio o fin para el rango de fechas", 400
                start_dates = generate_weekly_dates(start_date, end_date)

            app.logger.info(f"Fechas seleccionadas/generadas: {start_dates}")

            if not start_dates:
                app.logger.error("No se generaron fechas válidas")
                return "Error: No se generaron fechas válidas", 400

            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                app.logger.info(f"Archivo CSV guardado en: {file_path}")

                template_pdf_path = '/var/www/firmasclientes/PSR_Sign-In_Sheet_(2024)_Plantilla.pdf'
                main_output_dir = app.config['OUTPUT_FOLDER']
                create_weekly_pdfs_from_csv(file_path, template_pdf_path, main_output_dir, start_dates, time_period)

                app.logger.info(f"Contenido del directorio de salida antes de crear el ZIP: {os.listdir(main_output_dir)}")

                output_zip = os.path.join(app.config['OUTPUT_FOLDER'], 'output.zip')
                directories = [os.path.join(main_output_dir, d) for d in os.listdir(main_output_dir) if os.path.isdir(os.path.join(main_output_dir, d))]
                app.logger.info(f"Directorios para comprimir: {directories}")
                create_zip(output_zip, directories)

                app.logger.info(f"Contenido del directorio de salida después de crear el ZIP: {os.listdir(main_output_dir)}")

                @after_this_request
                def cleanup(response):
                    try:
                        app.logger.info(f"Iniciando limpieza de archivos")
                        if file_path and os.path.exists(file_path):
                            app.logger.info(f"Eliminando archivo subido: {file_path}")
                            os.remove(file_path)

                        for directory in directories:
                            for root, _, files in os.walk(directory):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    if os.path.isfile(file_path):
                                        app.logger.info(f"Eliminando archivo PDF: {file_path}")
                                        os.remove(file_path)
                            app.logger.info(f"Eliminando directorio de semana: {directory}")
                            os.rmdir(directory)

                        if os.path.isfile(output_zip):
                            app.logger.info(f"Eliminando archivo ZIP: {output_zip}")
                            os.remove(output_zip)

                    except Exception as e:
                        app.logger.error(f"Error durante la limpieza: {e}", exc_info=True)
                    return response

                return redirect(url_for('firmasclientes.download_file', filename='output.zip'))

        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error en upload_file: {e}", exc_info=True)
        return "Internal Server Error", 500

@bp.route('/uploads/<filename>')
def download_file(filename):
    try:
        app.logger.info(f"Intentando descargar el archivo: {filename}")
        zip_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        app.logger.info(f"Ruta del archivo ZIP: {zip_path}")

        if not os.path.isfile(zip_path):
            app.logger.error(f"El archivo {filename} no existe en {zip_path}")
            return "File not found", 404

        @after_this_request
        def cleanup(response):
            try:
                app.logger.info(f"Iniciando limpieza después de la descarga del archivo: {filename}")
                if os.path.isfile(zip_path):
                    app.logger.info(f"Eliminando archivo ZIP: {zip_path}")
                    os.remove(zip_path)

                directories = [os.path.join(app.config['OUTPUT_FOLDER'], d) for d in os.listdir(app.config['OUTPUT_FOLDER']) if os.path.isdir(os.path.join(app.config['OUTPUT_FOLDER'], d))]
                for directory in directories:
                    for root, _, files in os.walk(directory):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.isfile(file_path):
                                app.logger.info(f"Eliminando archivo PDF: {file_path}")
                                os.remove(file_path)
                    app.logger.info(f"Eliminando directorio de semana: {directory}")
                    os.rmdir(directory)

            except Exception as e:
                app.logger.error(f"Error durante la limpieza después de la descarga: {e}", exc_info=True)
            return response

        return send_from_directory(app.config['OUTPUT_FOLDER'], filename)
    except Exception as e:
        app.logger.error(f"Error en download_file: {e}", exc_info=True)
        return "Internal Server Error", 500

app.register_blueprint(bp)

if __name__ == '__main__':
    if not os.path.exists(app.config['OUTPUT_FOLDER']):
        os.makedirs(app.config['OUTPUT_FOLDER'])
    app.run(debug=True)

