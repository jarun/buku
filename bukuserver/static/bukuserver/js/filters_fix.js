$(document).ready(function () {
  const IDX = [[36, 'a'], [10, 'A'], [0, '0']];
  let idxChar = (i, [x, c]=IDX.find(([x]) => i >= x)) => String.fromCharCode(c.charCodeAt(0) + (i-x));
  filter_form.onsubmit = function () {
    $(`.filter-val[name]`, this).each((i, e) => {e.name = e.name.replace(/(?<=^flt)[^_]*(?=_)/, idxChar(i))});
  };
  $(`.pagination a:not([href^=javascript])`).each((_, e) => {
    let url = new URL(e.href), params = Array.from(new URLSearchParams(url.search)), idx = 0;
    params.forEach(kv => {
      let m = kv[0].match(/^flt[^_]*(_.*)$/);
      if (m) kv[0] = `flt${idxChar(idx++)}${m[1]}`;
    });
    e.href = Object.assign(url, {search: new URLSearchParams(params)});
  });
});
