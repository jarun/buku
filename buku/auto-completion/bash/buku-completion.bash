#
# Bash completion definition for buku.
#
# Author:
#   Arun Prakash Jana <engineerarun@gmail.com>
#

_buku () {
    COMPREPLY=()
    local IFS=$' \n'
    local cur=$2 prev=$3
    local -a opts opts_with_args
    opts=(-a --add -c --comment --deep -d --delete -e --export -h --help -i --import
          -k --unlock -l --lock -m --merge --noprompt -o --open -p --print -r --replace
          -s --sany -S --sall --st --stag --tag -t --title -u --update --url)
    opts_with_arg=(-a --add -e --export -i --import -m --merge
                   -o --open -r --replace -s --sany -S --sall --url)

    # Do not complete non option names
    [[ $cur == -* ]] || return 1

    # Do not complete when the previous arg is an option expecting an argument
    for opt in "${opts_with_arg[@]}"; do
        [[ $opt == $prev ]] && return 1
    done

    # Complete option names
    COMPREPLY=( $(compgen -W "${opts[*]}" -- "$cur") )
    return 0
}

complete -F _buku buku
