document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM completamente cargado y analizado');
    
    const form = document.getElementById('pdfForm');
    const submitButton = document.getElementById('submitButton');
    const dateOption = document.getElementById('date_option');
    const dateRangeFields = document.getElementById('date_range_fields');
    const specificDatesFields = document.getElementById('specific_dates_fields');
    const addDateButton = document.getElementById('add_date');
    const specificDatesContainer = document.getElementById('specific_dates_container');
    
    console.log('Formulario encontrado:', form);
    console.log('Botón de envío encontrado:', submitButton);

    function toggleDateFields() {
        console.log('Tipo de fecha seleccionado:', dateOption.value);
        if (dateOption.value === 'range') {
            dateRangeFields.style.display = 'block';
            specificDatesFields.style.display = 'none';
            document.querySelectorAll('#specific_dates_container input').forEach(input => input.required = false);
            document.getElementById('start_date').required = true;
            document.getElementById('end_date').required = true;
        } else {
            dateRangeFields.style.display = 'none';
            specificDatesFields.style.display = 'block';
            document.querySelectorAll('#specific_dates_container input').forEach(input => input.required = true);
            document.getElementById('start_date').required = false;
            document.getElementById('end_date').required = false;
        }
    }

    // Llamar a la función inicialmente y agregar el listener
    toggleDateFields();
    dateOption.addEventListener('change', toggleDateFields);

    // Función para añadir fechas específicas
    if (addDateButton) {
        addDateButton.addEventListener('click', function(e) {
            e.preventDefault();
            const newDateInput = document.createElement('input');
            newDateInput.type = 'date';
            newDateInput.name = 'specific_dates[]';
            specificDatesContainer.appendChild(newDateInput);
            toggleDateFields(); // Actualizar el estado de los campos required
        });
    }

    if (form) {
        form.addEventListener('submit', function(e) {
            console.log('Evento de envío del formulario capturado');
            e.preventDefault();
            
            const selectedOption = dateOption.value;
            let isValid = true;

            console.log('Opción seleccionada:', selectedOption);

            if (selectedOption === 'range') {
                const startDate = document.getElementById('start_date').value;
                const endDate = document.getElementById('end_date').value;
                console.log('Fecha de inicio:', startDate, 'Fecha de fin:', endDate);
                if (!startDate || !endDate) {
                    isValid = false;
                    alert('Por favor, seleccione una fecha de inicio y fin para el rango de fechas.');
                }
            } else {
                const specificDates = document.querySelectorAll('#specific_dates_container input[type="date"]');
                console.log('Fechas específicas:', Array.from(specificDates).map(input => input.value));
                if (specificDates.length === 0 || !Array.from(specificDates).some(input => input.value)) {
                    isValid = false;
                    alert('Por favor, seleccione al menos una fecha específica.');
                }
            }

            if (isValid) {
                console.log('Formulario válido, enviando...');
                form.submit();
            } else {
                console.log('Formulario no válido');
            }
        });
    } else {
        console.error('Formulario no encontrado en el DOM');
    }

    if (submitButton) {
        submitButton.addEventListener('click', function(e) {
            console.log('Botón de envío clickeado');
        });
    } else {
        console.error('Botón de envío no encontrado en el DOM');
    }
});