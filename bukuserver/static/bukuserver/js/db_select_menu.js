addEventListener('load', () => $(`.dbselector`).each((_, selector) => {
  let popup = selector.matches('.popup');
  let bookmark = () => $(`.admin-form input#link[type=url]`).attr('value') || $(`.table .link > a:not(.badge)`).attr('href');
  let _addFormParam = (form, name, value) => form.append( $(`<input type="hidden">`).attr('name', name).attr('value', value) );
  let addFormParams = (form, ...params) => params.reduce((f, kv) => (!kv ? f : _addFormParam(f, ...kv)), form)
  let fillForm = (name, form) => addFormParams(form, ['name', name], popup && ['url', bookmark()]);
  let modal = 'dbSelect' + (!popup ? '' : 'Popup') + 'Menu';
  let container = selector;
  while (container && !container.matches('.navbar-brand'))
    container = container.parentNode;
  container && $(container).on('contextmenu', evt => ($('#'+modal).modal('show'), evt.preventDefault()));
  $(selector).attr('data-toggle', 'modal').attr('data-target', '#'+modal).on('click', evt => evt.preventDefault());

  $(`body > .container`).first().append(`
    <div class="modal fade" id="${modal}" tabindex="-1" role="dialog" aria-labelledby="imageModal">
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${CURRENT_DB.title}</h5>
            <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span></button></div>
          <div class="modal-body"></div></div></div></div>`);
  $('#'+modal).on('show.bs.modal', function ({relatedTarget: e}) {
    fetch(CURRENT_DB.get).then(x => x.json()).then(({name, available}) => {
      let menu = $(`<div class="nav nav-pills flex-column">`);
      available.forEach(s => {
        let form = fillForm(s, $(`<form class="nav-item" method="POST">`).attr('action', CURRENT_DB.set))
          .append($(`<a class="nav-link" style="cursor: pointer">`).toggleClass('disabled', s == name).click(() => form.submit())
            .append( $(`<i class="fa ${s != name ? "fa-circle-o text-secondary" : "fa-check-circle text-success"}">`) )
            .append( $('<span class="ml-3">').text(s) ));
        menu.append(form);
      });
      $('.modal-body', this).html(``).append(menu);
    })});
}));
