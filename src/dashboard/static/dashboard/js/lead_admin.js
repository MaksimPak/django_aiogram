window.addEventListener('load', function() {
    (function($) {
        $('form').submit(function() {
            if ($('.field-is_client input:checkbox:checked').length > 0) {
                var c = confirm('Хотите продолжить ?');
                return c;
            }
        });
    })(django.jQuery);
});
