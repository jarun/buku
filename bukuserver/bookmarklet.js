// source for the bookmarklet in templates/bukuserver/bookmarklet.url:
//
// 1. paste this code in https://bookmarklets.org/maker/
// 2. replace contents of bookmarklet.url file with the result
//
// ("{{url}}" will be substituted with actual URL at runtime)

var url = location.href;
var title = document.title.trim() || "";
var desc = document.getSelection().toString().trim() || (document.querySelector('meta[name$=description i], meta[property$=description i]')||{}).content || "";
if(desc.length > 4000){
    desc = desc.substr(0,4000) + '...';
    alert('The selected text is too long, it will be truncated.');
}
url = "{{url}}" +
    "?url=" + encodeURIComponent(url) +
    "&title=" + encodeURIComponent(title) +
    "&description=" + encodeURIComponent(desc);
window.open(url, '_blank', 'menubar=no, height=600, width=600, toolbar=no, scrollbars=yes, status=no, dialog=1');
