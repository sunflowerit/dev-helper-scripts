#!/bin/bash

# configuration
# stop on any error
set -e
# separator
IFS="
"

# function to echo to stderr
echoerr() { echo "$@" >&2; }

# process command line parameters
GARBAGE_COLLECTION=1
ARG1=""
while [ $# -gt 0 ]; do
    key="$1"
    case $key in
        --skip-garbage-collection)
        GARBAGE_COLLECTION=0
        ;;
        *)
        if [[ $key != -* ]]; then
           ARG1=$key
        fi
        ;;
    esac
    shift # past argument or value
done

# decide buildout directory to use
if [ ! -d "$ARG1" ]; then
    BUILDOUT_USER=$ARG1
    BUILDOUT_DIR=$(sh -c "echo ~$BUILDOUT_USER/odoo")
else
    BUILDOUT_DIR=$ARG1
fi

# compute derived directories
BUILDOUT_CONFIG=$BUILDOUT_DIR/buildout.cfg
BUILDOUT_INCLUDE=$BUILDOUT_DIR/therp.cfg
EGG_DIR=$BUILDOUT_DIR/eggs
PART_DIR=$BUILDOUT_DIR/parts
START_SCRIPT=$BUILDOUT_DIR/bin/start_odoo

# sanity check: is this a usable buildout folder?
if [ ! -d $BUILDOUT_DIR ] || [ ! -f $BUILDOUT_CONFIG ]; then
    echoerr I need a user with a standard buildout
    echoerr or a directory that points to a buildout
    echoerr couldn\'t find $BUILDOUT_DIR or $BUILDOUT_CONFIG
    exit 1
fi

if [ ! -d $EGG_DIR ] || [ ! -d $PART_DIR ] || [ ! -x $START_SCRIPT ]; then
    echoerr Did you ever build your buildout? I expect $EGG_DIR, $PART_DIR
    echoerr and $START_SCRIPT to exist
    exit 1
fi

ODOO_VERSION="$(grep '^oca_branch_version.*=.*'\
    $BUILDOUT_INCLUDE | cut -d= -f2 | tr -d '[[:space:]]')"
# default to 8.0 if not found
if [ -z "$ODOO_VERSION" ]; then
    ODOO_VERSION="8.0"
    echoerr couldn\'t find oca_branch_version, defaulting to $ODOO_VERSION >&2
fi
# mapping from parts to branches
PART_BRANCH=$(mktemp)

# say get_field $line $fieldnumber (1 based)
get_field()
{
    echo "$1" | awk -F'( +)+' '{print $'"$2"'}'
}

# say get_branch_params "$line"
# return value is branch|params
get_branch_params()
{
    # $params can (and will later) contain a hint in which
    # branch our commit lives
    params=$(get_field "$1" 6)
    if echo $params | grep -q 'branch='; then
        branch=$(echo $params | grep -qEo 'branch=[^,]+' |\
            cut -c -7)
    else
        branch=$(get_field "$line" 5 |\
            sed 's/${buildout:oca_branch_version}/'$ODOO_VERSION'/g')
        # if what we got something that looks like a hash as branch name
        # treat it likewise
        if echo $branch | grep -iEq "^[0-9a-z]{6,}$"; then
            branch=$ODOO_VERSION
        fi
        params="$params${params:+,}branch=$branch"
    fi
    echo $branch\|$params
}

# say handle_source_line "$line"
# return a line with hash pin or nothing if no hash is found
handle_source_line()
{
    line="$1"
    vcs=$(get_field "$line" 2)
    url=$(get_field "$line" 3)
    path=$(get_field "$line" 4)
    branch=$(get_branch_params "$line" | cut -d\| -f1)
    params=$(get_branch_params "$line" | cut -d\| -f2)
    abspath=$BUILDOUT_DIR/$path
    # you don't need the parts directory everywhere
    if [ ! -d $abspath ]; then
        abspath=$BUILDOUT_DIR/parts/$path
        echo "parts/$path|$branch" >> $PART_BRANCH
    fi
    # get merge head
    hash=$(git -C $abspath show-branch --merge-base \
        origin/$branch \
        $branch |\
        cut -c -7)
    if [ ! -z "$hash" ]; then
        echo "$vcs $url $path $hash $params"
        echo "$path|$branch" >> $PART_BRANCH
    fi
}

# say handle_version_line "$line"
# return a version line with hash pin
handle_version_line()
{
    line=$(echo "$1" | awk -F' *= *' '{print $2}')
    echo "version = $(handle_source_line " $line")"
}

for line in $(cat $BUILDOUT_CONFIG); do
    print_line=""
    if [ -z "$line" ] || echo $line | grep -qE '^#'; then
        echo "$line"
        continue
    fi
    # find [section_header] lines
    if echo $line | grep -q '^[[][^]]*]'; then
        current_section=$(echo $line | tr -d '[]')
        # for the odoo section, we slip in the version line if not already done
        if grep -q '^version *=' $BUILDOUT_INCLUDE &&\
                ! grep -q '^version *=' $BUILDOUT_CONFIG &&\
                [ "$current_section" = "odoo" ]; then
            line=$(printf "%s\n%s" $line \
                $(handle_version_line $(grep '^version *=' $BUILDOUT_INCLUDE)))

        fi
    # could also start a addons += block
    elif echo $line | grep -qE '^[^#].*+{0,1}='; then
        current_var=$(get_field "$line" 1)
        # for addons, slip in web, server-tools and therp-addons if necessary
        if [ "$current_var" = "addons" ]; then
            for repo in web therp-addons server-tools; do
                regex="(OCA|odoo|therp)/$repo(.git){0,1} *parts/$repo"
                if ! grep -iqE $regex $BUILDOUT_CONFIG; then
                    line=$(printf "%s\n    %s" "$line" \
                        $(handle_source_line \
                            $(grep -m1 $repo $BUILDOUT_INCLUDE)))
                fi
            done
        fi
    # an indented block from $current_var
    elif [ -n "$current_var" ] && echo $line | grep -qE '^[[:space:]]+|#'; then
        case $current_var in
            addons)
                vcs=$(get_field "$line" 2)
                case $vcs in
                    git)
                        pinned=$(handle_source_line "$line")
                        if [ ! -z "$pinned" ]; then
                            echo "    $pinned"
                            print_line="no"
                        fi
                    ;;
                    # we ignore bazaar, doesn't seem worth the effort for a
                    # dying vcs
                esac
            ;;
            merges)
                vcs=$(get_field "$line" 2)
                url=$(get_field "$line" 3)
                path=$(get_field "$line" 4)
                case $vcs in
                    git)
                        branch=$(get_branch_params "$line" | cut -d\| -f1)
                        params=$(get_branch_params "$line" | cut -d\| -f2)
                        abspath=$BUILDOUT_DIR/$path
                        head_branch=$(grep $path\| $PART_BRANCH | cut -d\| -f2)
                        if [ -z "$head_branch" ]; then
                            echo "$line"
                            continue
                        fi
                        # try to generate a readable unique local branch name
                        local_branch=$branch-$(echo $url | tr -cd 'A-Za-z0-9_-')
                        if ! git -C $abspath fetch --quiet $url\
                                $branch:$local_branch; then
                            # this most probably was rebased and force pushed
                            git -C $abspath branch -D $local_branch
                            git -C $abspath fetch --quiet $url\
                                $branch:$local_branch
                        fi
                        if git -C $abspath merge-base --is-ancestor \
                                $local_branch origin/$head_branch; then
                            echo '# this branch is merged already fully'
                            echo '#'$line
                        else
                            hash=$(git -C $abspath show-branch --merge-base \
                                $head_branch \
                                $local_branch)
                            echo "    $vcs $url $path $hash $params"
                        fi
                        print_line="no"
                    ;;
                esac
            ;;
        esac
    # everything else
    else
        current_var=""
    fi
    # skip versions because we write a new one
    if [ "$current_section" = "versions" ]; then
        continue
    fi
    if [ -z "$print_line" ]; then
        echo "$line"
    fi
done
echo '[versions]'
for dir in $EGG_DIR/*.egg; do
    if [ ! -d "$dir" ]; then
        continue
    fi
    egg=$(basename $dir .egg)
    egg=${egg%%-py*}
    version=${egg##*-}
    name=${egg%%-*}
    if [ "$name" = "pip" ] || [ "$name" = "zc.buildout" ] ||
       [ "$name" = "zc.recipe.egg" ]; then
        continue
    fi
    # only pin eggs named in our startup script
    if grep -q $egg $START_SCRIPT; then
        echo "$name = $version"
    fi
done
rm $PART_BRANCH
# only do this in the end to keep commits floating
# around when analyzing merges. this will save us a lot of time
# fetching stuff above

# Garbage collect git branches
#if [ -z $GARBAGE_COLLECTION ]
if [ $GARBAGE_COLLECTION -eq "1" ]; then
echoerr garbage collecting branches \(you can Ctrl-C this if you\'re \
in a hurry\)
for dir in $PART_DIR/*; do
    git -C $dir gc --quiet
done
fi
