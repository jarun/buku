$(document).ready(function () {  // retaining state of same-kind filters on switch
  let config = JSON.parse(document.getElementById('filter-groups-data').innerText);
  let isOrder = k => config[k]?.[0].arg.startsWith('order_');
  let orderFilters = () => $(`option[value^="order_"]`).parent(`.filter-op`);
  let filterInput = filter => $(`:is(input, select).filter-val`, $(filter).parents('tr').first());
  let adder = $(`.field-filters .filter`).filter(function () {return isOrder(this.innerText)}).get(0);
  let stickyValue = (filter, input=filterInput(filter)) => $(filter).on('change', (evt, param) => {
    let _input = filterInput(filter);
    if (evt.removed?.id?.startsWith('order_by_') == evt.val?.startsWith('order_by_'))
      _input.val( input.val() );  // retaining the last value
    input = _input;
    if (input.prop('tagName') == 'SELECT')  // redraw select widget
      $(`.select2-chosen`, input.prev()).text( $(':selected', input).text() );
  });
  orderFilters().each(function () {stickyValue(this)});
  adder.onclick = () => setTimeout(() => stickyValue( orderFilters().last() ));
});
