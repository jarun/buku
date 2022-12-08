// source for the bookmarklet in templates/bukuserver/home.html:
//
// 1. paste this code in https://bookmarklets.org/maker/
// 2. copy the result to home.html in the bookmarklet anchor href
// 3. Replace "URL_FOR" with "{{url_for("bookmarklet",_external=True)}}"

var url = location.href;
var title = document.title.trim() || "";
var desc = document.getSelection().toString().trim() || (document.querySelector('meta[name$=description i], meta[property$=description i]')||{}).content || "";
if(desc.length > 4000){
    desc = desc.substr(0,4000) + '...';
    alert('The selected text is too long, it will be truncated.');
}
url = "URL_FOR" +
    "?url=" + encodeURIComponent(url) +
    "&title=" + encodeURIComponent(title) +
    "&description=" + encodeURIComponent(desc);
window.open(url, '_blank', 'menubar=no, height=600, width=600, toolbar=no, scrollbars=yes, status=no, dialog=1');
