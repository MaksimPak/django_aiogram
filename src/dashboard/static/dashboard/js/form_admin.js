window.addEventListener('load', function() {
    (function($) {
        $('.field-custom_answer input:checkbox').change(function() {
        console.log(123123123)
            if (this.checked) {
                $('.field-custom_answer_text').show()
            }
            else {
                $('.field-custom_answer_text').hide()
            }
        })
    })(django.jQuery);
});
