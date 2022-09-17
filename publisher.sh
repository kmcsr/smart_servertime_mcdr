#!/bin/bash

COMMIT=true
RELEASE=true

while [ -n "$1" ]; do
	case $1 in
		-p | --packet-only)
			COMMIT=''
			RELEASE=''
			;;
		-C | --no-commit)
			COMMIT=''
			;;
		-R | --no-release)
			RELEASE=''
			;;
	esac
	shift
done

cd $(dirname $0)

echo '==> Reading plugin metadata...'
echo

_PARSER=$(cat <<EOF
import json,sys
o = json.load(open(sys.argv[1],"r"))
n, d, v, m = o["name"], o["id"], o["version"], o.get("archive_name")
print((n.replace(" ", "") if n else d) + "-v" + v if not m else m.format(id=d, version=v), v)
EOF
)
_TG='mcdreforged.plugin.json'
data=($(python3 -c "$_PARSER" "$_TG"))
if [ $? -ne 0 ]; then
	echo
	echo "[ERROR] Cannot parse '${_TG}'"
	exit 1
fi
name="${data[0]}"
version="v${data[1]}"

echo '==> Packing source files...'
python3 -m mcdreforged pack -o ./output -n "$name" || exit $?

if [ -n "$COMMIT" ]; then

echo '==> Commiting git repo...'
( git add . && git commit -m "$version" && git push ) || exit $?

fi

if [ -n "$RELEASE" ]; then

echo '==> Creating github release...'
gh release create "$version" "./output/${name}.mcdr" -t "$version" -n '' || exit $?

fi

echo '==> Done'
