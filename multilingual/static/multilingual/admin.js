(function($) {
    $(function() {
        $('#remove-translations').click(function(e) {
            return confirm(
                'Are you sure? This will delete translations for all translated languages.'
            );
        });
    });
})(django.jQuery);
