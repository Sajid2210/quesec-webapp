document.addEventListener('DOMContentLoaded', function () {
    const isParentCheckbox = document.querySelector('#id_is_parent');
    const parentField = document.querySelector('#id_parent');
    const linkField = document.querySelector('#id_link');

    function toggleFields() {
        if (isParentCheckbox.checked) {
            parentField.disabled = true;
        } else {
            parentField.disabled = false;
        }
    }

    if (isParentCheckbox) {
        toggleFields();  // Initial check
        isParentCheckbox.addEventListener('change', toggleFields);
    }
});
