window.addEventListener('load', function() {
    (function($) {
        $('.field-custom_answer input:checkbox').change(function() {
            if (this.checked) {
                $('.field-custom_answer_text').show();
            }
            else {
                $('.field-custom_answer_text').hide();
            }
        })

        $('.flat-json-toggle-textarea').hide();


        setTimeout(divWriter, 50)
        $('a.flat-json-add-row').on('click', () => {setTimeout(divWriter, 0)})

        function divWriter() {
            const rows = $('.flat-json-rows')
            const elements = rows.find('.form-row')

            elements.each(function() {
                let writeDiv = $(this).find('.writeDiv')

                $(this).find('.flat-json-value').hide();
                const child = $(this).find('.flat-json-value')

                if(!writeDiv.length) {
                    html = `<div class='writeDiv' contenteditable=true>${child.val()}</div>`
                    $(this).find('.flat-json-remove-row').before(html)
                }

                const textDiv = $(this).find('.writeDiv')
                textDiv.on('change keyup paste input', (data) => {
                    const text = data.target.innerText.replace(/(?:\r\n|\r|\n)/g, '<br>');

                    if (text.substr(text.length - 4) == '<br>') {
                        child.val(text.substr(0, text.length - 4)).trigger('input');
                    } else {
                        child.val(text).trigger('input');
                    }
                })
            })
        }

    })(django.jQuery);
});
