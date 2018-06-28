$(document).ready(function() {
  $.getJSON( "/api/tags", function( json ) {
    $('input#tags').select2({
      tags: json.tags,
      tokenSeparators: [','],
    });
  });
});
