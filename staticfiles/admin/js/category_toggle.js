document.addEventListener('DOMContentLoaded', function () {
    const isParentCheckbox = document.querySelector('#id_is_parent');
    const parentDropdown = document.querySelector('#id_parent');

    function toggleParentField() {
        if (isParentCheckbox.checked) {
            parentDropdown.disabled = true;
        } else {
            parentDropdown.disabled = false;
        }
    }

    if (isParentCheckbox && parentDropdown) {
        toggleParentField();
        isParentCheckbox.addEventListener('change', toggleParentField);
    }
});
