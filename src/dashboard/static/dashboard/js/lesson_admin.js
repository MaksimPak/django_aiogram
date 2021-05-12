window.addEventListener('load', function() {
    (function($) {
        if ($('.field-has_homework input:checkbox:checked').length === 0)
        {
            $('.field-homework_desc').attr('hidden', true)
        }
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
