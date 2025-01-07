_snaprepo_completion() {
    local cur prev cmd used_opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD - 1]}"
    cmd="${COMP_WORDS[1]}"
    
    # Track used options
    used_opts=()
    for ((i=1; i < COMP_CWORD; i++)); do
        [[ "${COMP_WORDS[i]}" == -* ]] && used_opts+=("${COMP_WORDS[i]}")
    done

    local commands="snap tokens completion stream"
    local default_opts="--path --max-file-size --skip-common --skip-files --help"

    # First word completion
    if [[ $COMP_CWORD -eq 1 ]]; then
        COMPREPLY=($(compgen -W "${commands} ${default_opts}" -- "${cur}"))
        return 0
    fi

    # Handle --skip-files specially
    if [[ "$prev" == "--skip-files" ]]; then
        compopt -o default
        return 0
    fi

    case "$prev" in
        --path|-p)
            compopt -o dirnames
            return 0
            ;;
        --output|-o)
            compopt -o default
            return 0
            ;;
    esac

    # Filter out used single-use options
    filter_opts() {
        local opts=($1)
        local filtered=""
        for opt in "${opts[@]}"; do
            if [[ ! " ${used_opts[@]} " =~ " ${opt} " ]] || [[ "$opt" == "--skip-files" ]]; then
                filtered+="$opt "
            fi
        done
        echo "$filtered"
    }

    case "$cmd" in
        ""|snap|stream)
            if [[ "${cur}" == -* ]]; then
                local opts
                case "$cmd" in
                    snap) opts="--path --output --summary --no-summary --max-file-size --force --skip-common --skip-files --help" ;;
                    stream) opts="--path --max-file-size --skip-common --skip-files --help" ;;
                    *) opts="$default_opts" ;;
                esac
                COMPREPLY=($(compgen -W "$(filter_opts "$opts")" -- "${cur}"))
            fi
            ;;
        tokens)
            compopt -o default
            ;;
        completion)
            COMPREPLY=($(compgen -W "bash zsh fish" -- "${cur}"))
            ;;
    esac
}

complete -F _snaprepo_completion snaprepo