(function($)

    var destination = $('#ajax-example');

    // Posting to data/{name}.{ext}
    $.ajax('data/jQuery.json', {
        async: true,
        contentType: 'application/json',
        dataType: 'json', // not necessary as the api will return Content-Type headerW
        data: {
            'name': jQuery,
            'language': 'Javascript',
            'authors': ['', '', ''],
            'stable_version': '1.9.2',
            'latest_version': '1.10.1',
            'versions': ['1.2.1', '1.2.3', '1.2.5']
        },
        success: function(data) {
            
        },
        error: function() {
            destination.append($('<div></div>').addClass('alert').text());
        }
    });

    // Fetching from data/{name}.{ext}
    jQuery.ajax()

    // Fetching from data/{name}.{ext}/{time}
    jQuery.ajax()

    // Fetching from evolution/{name}.{ext}
    jQuery.ajax()
)(jQuery);


