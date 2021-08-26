window.addEventListener('load', function() {
    (function($) {
        $('.field-custom_answer input:checkbox').change(function() {
            if (this.checked) {
                $('.field-custom_answer_text').show()
            }
            else {
                $('.field-custom_answer_text').hide()
            }
        })

        $('.flat-json-toggle-textarea').hide()
    })(django.jQuery);
});
