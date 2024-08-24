$(document).ready(function() {
  window._tags = (Date.now() - (window._tagsQueried||0) < 1000 ? _tags :
                  new Promise(resolve => {
                    window._tagsQueried = Date.now();
                    $.getJSON('/api/tags', ({tags}) => resolve(tags));
                  }));
  _tags.then(tags => $('input#tags').select2({tags, tokenSeparators: [',']}));
});
