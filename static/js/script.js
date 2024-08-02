document.addEventListener('DOMContentLoaded', function() {
    const dateOption = document.getElementById('date_option');
    const dateRangeFields = document.getElementById('date_range_fields');
    const specificDatesFields = document.getElementById('specific_dates_fields');

    dateOption.addEventListener('change', function() {
        if (this.value === 'range') {
            dateRangeFields.style.display = 'block';
            specificDatesFields.style.display = 'none';
        } else {
            dateRangeFields.style.display = 'none';
            specificDatesFields.style.display = 'block';
        }
    });

    const addDateButton = document.getElementById('add_date');
    const specificDatesContainer = document.getElementById('specific_dates_container');

    addDateButton.addEventListener('click', function() {
        const newDateInput = document.createElement('input');
        newDateInput.type = 'date';
        newDateInput.name = 'specific_dates[]';
        newDateInput.required = true;
        specificDatesContainer.appendChild(newDateInput);
    });
});
document.addEventListener('DOMContentLoaded', function() {
    const dateOption = document.getElementById('date_option');
    const dateRangeFields = document.getElementById('date_range_fields');
    const specificDatesFields = document.getElementById('specific_dates_fields');

    dateOption.addEventListener('change', function() {
        if (this.value === 'range') {
            dateRangeFields.style.display = 'block';
            specificDatesFields.style.display = 'none';
        } else {
            dateRangeFields.style.display = 'none';
            specificDatesFields.style.display = 'block';
        }
    });

    const addDateButton = document.getElementById('add_date');
    const specificDatesContainer = document.getElementById('specific_dates_container');

    addDateButton.addEventListener('click', function() {
        const newDateInput = document.createElement('input');
        newDateInput.type = 'date';
        newDateInput.name = 'specific_dates[]';
        newDateInput.required = true;
        specificDatesContainer.appendChild(newDateInput);
    });
});
