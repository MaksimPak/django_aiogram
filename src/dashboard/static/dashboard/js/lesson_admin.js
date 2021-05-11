window.addEventListener('load', function() {
    (function($) {
        $('#id_has_homework').change(function() {
            if (this.checked) {
                $('.field-homework_desc').show()
            }
            else {
                $('.field-homework_desc').hide()
            }
        })
    })(django.jQuery);
});
