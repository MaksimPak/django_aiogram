window.addEventListener('load', function() {
    (function($) {
        $('#changelist-filter-clear').remove()
        $('#changelist-filter li:first-child').remove()
        $('#changelist-filter li:last-child').remove()
    })(django.jQuery);
});
