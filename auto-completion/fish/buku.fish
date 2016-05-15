#
# Fish completion definition for buku.
#
# Author:
#   Arun Prakash Jana <engineerarun@gmail.com>
#
complete -c buku -s a -l add    -r  --description 'add bookmark'
complete -c buku -s d -l delete     --description 'delete bookmark'
complete -c buku -s h -l help       --description 'show help'
complete -c buku -s k -l unlock     --description 'decrypt database'
complete -c buku -s l -l lock       --description 'encrypt database'
complete -c buku -s o -l open    -r --description 'open bookmark in browser'
complete -c buku -s p -l print      --description 'show bookmark details'
complete -c buku -s r -l replace -r --description 'replace a tag'
complete -c buku -s s -l sany    -r --description 'search any keyword'
complete -c buku -s S -l sall    -r --description 'search all keywords'
complete -c buku -s t -l title      --description 'set custom title'
complete -c buku -s u -l update     --description 'update bookmark'
