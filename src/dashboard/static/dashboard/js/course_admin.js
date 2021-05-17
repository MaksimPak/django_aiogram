window.addEventListener('load', function() {
    (function($) {
        $('.receivedVid').each((idx, val) => {
            if ($(val).children('a').length == 0) {
                $(val).children('button').attr('hidden', true);
            }
        })

        $('.viewedVid').each((idx, val) => {
            if ($(val).children('a').length == 0) {
                $(val).children('button').attr('hidden', true);
            }
        })

        $('.hwSubmitted').each((idx, val) => {
            if($(val).children('a').length == 0) {
                $(val).children('button').attr('hidden', true);
            }
        })
    })(django.jQuery);
});
