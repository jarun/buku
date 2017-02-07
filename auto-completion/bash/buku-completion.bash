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
    opts=(
        -a --add
        -c --comment
        -d --delete
        --deep
        -e --export
        --expand
        -f --format
        -h --help
        -i --import
        --immutable
        -j --json
        -k --unlock
        -l --lock
        -m --merge
        --nc
        --np
        -o --open
        --oa
        -p --print
        -r --replace
        -s --sany
        -S --sall
        --shorten
        --sreg
        --stag
        -t --title
        --tacit
        --tag
        --threads
        -u --update
        --url
        -V
        -v --version
        -w --write
        -z --debug
    )
    opts_with_arg=(
        -a --add
        -e --export
        --expand
        -f --format
        -i --import
        --immutable
        -m --merge
        -r --replace
        -s --sany
        -S --sall
        --shorten
        --sreg
        --threads
        --url
    )

    if [ "$prev" == "--stag" ]; then
        COMPREPLY=( $(compgen -W "$(buku --completion tags)" -- "$cur") )
        return 0
    fi

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
