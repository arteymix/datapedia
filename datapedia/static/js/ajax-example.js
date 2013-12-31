$(document).ready(function() {

    // Posting to data/{name}.{ext}
    $.ajax('/data/jQuery.json', {
        async: true,
        contentType: 'application/json',
        dataType: 'json', // not necessary as the api will return Content-Type headerW
        data: {
            'name': 'jQuery',
            'language': 'Javascript',
            'authors': ['John Resig', 'Gilles van den Hoven', 'Michael Geary'],
            'releases': [{
                'minified': 'http://code.jquery.com/jquery-2.0.2.min.js',
                'uncompressed': 'http://code.jquery.com/jquery-2.0.2.js',
                'version': '2.0.2',
            }],
        },
        success: function(data) {

            $('#ajax-example')
                .append($('<div></div>')
                    .addClass('alert alert-success')
                    .text('Current jQuery was fetched with success!'));

            var table = $("<table class='table'></table>")

            $.each(data, function(key, value) {
                table.append($('<tr>' + key '</li>')
                    .append('<th>' + key + '</th>')
                    .append('<th>' + key + '</th>'));
            });


            $('#ajax-example')
                .append(table);
        },
        error: function(error) {
            console.log(error);
            $('#ajax-example').append($("<div class='alert alert-block alert-danger'></div>")
                .append('<h4>Could not POST data for jQuery.json</h4>')
                .append($("<ul class='unstyled'></ul>").append(function() {
                    $.each(error, function(field, errors) {
                        $(this).append($('<li></li>').text(
                            $.each(errors, function(index, message) {
                                $(this).append('<p>' + message + '</p>');    
                            })
                        ))    
                    }    
                }))
                .text('Could not send data for jQuery. ' + error));
        },
        complete: console.log,
    });

    // Fetching from data/{name}.{ext}
    jQuery.ajax();

    // Fetching from data/{name}.{ext}/{time}
    jQuery.ajax();

    // Fetching from evolution/{name}.{ext}
    jQuery.ajax();

});
