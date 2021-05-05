window.addEventListener('load', function() {
    (function($) {
        $('form').submit(function() {
            var c = confirm('Хотите продолжить ?');
            return c;
        })
    })(django.jQuery);
});
