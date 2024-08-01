from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/firmasclientes', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Aquí irá la lógica de procesamiento del formulario
        pass
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
