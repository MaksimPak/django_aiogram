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

        console.log($('#form_form').serialize());

    })(django.jQuery);
});
