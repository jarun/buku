$(document).ready(function () {  // synchronizing buku filters
  let bukuFilters = () => $(`option[value^="buku_"]`).parent(`.filter-op`);
  let filterInput = filter => $(`.filter-val`, $(filter).parents('tr').first());
  let adder = $(`.field-filters .filter`).filter(function () {return this.innerText === 'buku'}).get(0);
  let sync = (key, $filter=bukuFilters().last(), value=filterInput($filter).val()) => {
    ($filter.val() != key) && $filter.val(key).triggerHandler('change');
    filterInput($filter).val(value).trigger('focus').on('change', evt => {value = evt.target.value});
    $filter.on('change', (evt, param) => (param == '$norecur$') || bukuFilters().each(function () {
      if (this == evt.target) {
        filterInput(this).val(value);  // retaining the last filter value
      } else {
        let _value = filterInput(this).val();
        $(this).val(evt.val).triggerHandler('change', '$norecur$');
        filterInput(this).val(_value);  // retaining the last value for other filters
      }
    }));
  };
  bukuFilters().each(function () {sync(this.value, $(this))});
  adder.onclick = () => {
    try {
      let key = bukuFilters().first().val() || 'buku_search_markers_match_all';
      setTimeout(() => sync(key));
    } catch (e) {  // ensuring the handler always returns false
      console.error(e);
    }
    return false;
  };
});
