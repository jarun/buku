$(document).ready(function() {
  $(`.pagination :contains("»") a`).not(`[href^="javascript:"]`).attr('href', (idx, href) =>
    href.replace(/\/?(\?|$)/, '/last-page$1').replace(/([?&])page=[0-9]+(&|$)/, '$1'));
});
