addEventListener('load', () => $(`.dbselector`).each((_, selector) => {
  let popup = selector.matches('.popup');
  let modal = 'dbSelect' + (!popup ? '' : 'Popup') + 'Menu';
  let container = selector;
  while (container && !container.matches('.navbar-brand'))
    container = container.parentNode;
  container && $(container).on('contextmenu', evt => ($('#'+modal).modal('show'), evt.preventDefault()));
  $(selector).attr('data-toggle', 'modal').attr('data-target', '#'+modal).on('click', evt => evt.preventDefault());

  let _param = Boolean(new URLSearchParams(location.search).get('db'));
  !popup && _param && (container?.classList.add('db-param'), selector.classList.add('text-success'));

  let bookmarkData = () => ({
    url: $(`.admin-form input#link[type=url]`).prop('value') || $(`.table .link > a:not(.badge)`).attr('href'),
    title: $(`.admin-form input#title`).prop('value') || $(`.table .title`).text(),
    tags: $(`.admin-form #s2id_tags .select2-search-choice, .table .tag-list .badge`).toArray().map(e => e.innerText).join(),
    description: $(`.admin-form textarea#description`).prop('value') || $(`.table .description`).data('source') || $(`.table .description`).text(),
  });

  let params = (...args) => `${new URLSearchParams(...args)}`;
  let adjustUrl = (url, db) => {
    let _url = new URL(url),  _params = new URLSearchParams(_url.search);
    (!db ? _params.delete('db') : _params.set('db', db));
    _url.search = _params;
    return `${_url}`;
  };

  let fail = (name="", error="Request failed") => setTimeout(() => {
    $('#'+modal).modal('hide');
    $('nav').first().after(
      $(`<div role="alert" class="alert alert-danger alert-dismissible fade show">`)
        .append( $(`<span>`).text(error + (name && ` (name='${name}')`)) )
        .append( $(`<button class="close" data-dismiss="alert">`).html('&times;')));
  }, 500);


  let submit = (name, {persist=_param}={}) => Promise.resolve( $('#'+modal).modal('hide') )
    .then(() => fetch(CURRENT_DB.api, {method: 'POST', body: params({name}), headers: {'Content-Type': 'application/x-www-form-urlencoded'}}))
    .then(response => response.json().then(_response => {
      if (!response.ok)
        fail(name, _response.message);
      else
        location.href = (!popup ? adjustUrl(location.href, persist && name) : CURRENT_DB.bookmarklet + '?' + params(bookmarkData()));
    })).catch(() => fail(name));

  $(`body > .container`).first().append(`
    <div class="modal fade" id="${modal}" tabindex="-1" role="dialog" aria-labelledby="imageModal">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${CURRENT_DB.title}</h5>
            <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button></div>
          <label class="form-check mx-3 my-2" role="button" title="${CURRENT_DB.retainTooltip}">
            <input id="${modal}-persist" type="checkbox" class="form-check-input"/>
            <span class="form-check-label">${CURRENT_DB.retainCaption}</span></label>
          <div class="modal-body"></div></div></div></div>`);
  $('#'+modal).on('show.bs.modal', function () {
    fetch(CURRENT_DB.api).then(x => (!x.ok ? fail() : x.json())).then(({name, available}) => {
      popup && $(`#${modal}-persist`).parent().remove();
      $(`#${modal}-persist`).prop('checked', _param);
      let menu = $(`<ul class="nav nav-pills flex-column">`);
      available.forEach(s => menu.append($(`<li>`)
          .append($(`<a class="nav-link" style="cursor: pointer">`).click(() => submit(s, {persist: $(`#${modal}-persist`).prop('checked')}))
            .append( $(`<i class="fa ${s != name ? "fa-circle-o text-secondary" : "fa-check-circle text-success"}">`) )
            .append( $('<span class="ml-3">').text(s) ))));
      $('.modal-body', this).html(``).append(menu);
    }).catch(() => fail());
  });
}));
