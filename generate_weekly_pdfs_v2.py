import os
import zipfile
import io
from flask import Flask, request, render_template, send_from_directory, redirect, url_for, after_this_request
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/var/www/firmasclientes/uploads'
app.config['OUTPUT_FOLDER'] = '/var/www/firmasclientes/output'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

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

def create_weekly_pdfs_from_csv(csv_path, template_pdf_path, main_output_dir, start_dates, time_period):
    if time_period == 'morning':
        times = ['08:00 AM / 12:15 PM'] * 5
    elif time_period == 'afternoon':
        times = ['12:45 PM / 05:00 PM'] * 5

    df = pd.read_csv(csv_path)

    for start_date in start_dates:
        week_from = pd.to_datetime(start_date)

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

def fill_pdf(template_path, output_path, data):
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

def generate_weekly_dates(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    week_dates = []

    current_date = start_date
    while current_date <= end_date:
        week_dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += pd.DateOffset(weeks=1)

    return week_dates

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        option = request.form['option']
        time_period = request.form['time_period']

        if option == 'specific_dates':
            dates = request.form['specific_dates']
            start_dates = dates.split(',')
        else:
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            start_dates = generate_weekly_dates(start_date, end_date)

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            template_pdf_path = '/var/www/firmasclientes/PSR_Sign-In_Sheet_(2024)_Plantilla.pdf'
            main_output_dir = app.config['OUTPUT_FOLDER']
            create_weekly_pdfs_from_csv(file_path, template_pdf_path, main_output_dir, start_dates, time_period)

            output_zip = os.path.join(app.config['OUTPUT_FOLDER'], 'output.zip')
            create_zip(output_zip, [os.path.join(main_output_dir, f) for f in os.listdir(main_output_dir) if f.endswith('.pdf')])

            @after_this_request
            def cleanup(response):
                os.remove(file_path)
                for pdf_file in os.listdir(main_output_dir):
                    file_path = os.path.join(main_output_dir, pdf_file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                return response

            return redirect(url_for('download_file', filename='output.zip'))

    return render_template('upload.html')

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['OUTPUT_FOLDER']):
        os.makedirs(app.config['OUTPUT_FOLDER'])
    app.run(debug=True)
