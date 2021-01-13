import os
import ast
import argparse
import os.path
import yaml


parser = argparse.ArgumentParser("kutana-i18n", description="Run kutana i18n related tasks.")
subparsers = parser.add_subparsers(help="action to perform", dest="action", required=True)

parser_collect = subparsers.add_parser("collect", help="collect translation string from sources")
parser_collect.add_argument(
    "--collect_from", "-c", dest="collect_from",
    default=os.getcwd(), help="path to search for sources"
)
parser_collect.add_argument(
    "--save_to", "-s", dest="save_to",
    default="i18n.yml", help="file to save results to"
)


def get_static_value(node):
    if node and node.__class__.__name__ == "Constant":
        return node.value
    return None


def collect_from_file(path, translation):
    with open(path, "r") as fh:
        content = fh.read()

    alias = ""

    root = ast.parse(content)

    for node in ast.walk(root):
        if node.__class__.__name__ == "ImportFrom":
            if node.module not in ["kutana", "kutana.i18n"]:
                continue

            for name in node.names:
                if name.name == "t":
                    alias = name.asname or "t"

        if (alias and node.__class__.__name__ == "Call"
                and node.func.__class__.__name__ == "Name"
                and node.func.id == alias):
            msgid = get_static_value(node.args[0] if node.args else None)
            known_kwargs = {kw.arg: get_static_value(kw.value) for kw in node.keywords}
            ctx = known_kwargs.get("ctx")
            num = "num" in known_kwargs

            key = (msgid, ctx or "")
            pointer = f"{path}:{node.lineno}:{node.col_offset + 1}"

            if key in translation:
                translation[key]["$where"].append(pointer)
            else:
                translation[key] = {
                    "msgid": msgid,
                    "msgstr": [] if num else "",
                    **({"msgctx": ctx} if ctx else {}),
                    "$where": [pointer],
                }


def collect(path, target):
    translation = {}

    if os.path.isfile(target):
        with open(target, "r") as fh:
            for string in yaml.safe_load(fh.read()):
                key = (string["msgid"], string.get("msgctx") or "")

                translation[key] = {
                    "msgid": string["msgid"],
                    "msgstr": string["msgstr"],
                    **({"msgctx": string["msgctx"]} if string.get("msgctx") else {}),
                    "$where": [],
                }

    for dirpath, __, filenames in os.walk(os.getcwd()):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue

            collect_from_file(
                os.path.relpath(os.path.join(dirpath, filename), os.getcwd()),
                translation
            )

    if os.path.dirname(target):
        os.makedirs(os.path.dirname(target), exist_ok=True)

    with open(target, "w") as fh:
        for translation in sorted([t for t in translation.values() if t["$where"]], key=lambda t: t["$where"]):
            where = translation.pop("$where", [])
            print("# " + "\n# ".join(where), file=fh)
            print(yaml.safe_dump([translation], allow_unicode=True), file=fh)

        if not fh.tell():
            fh.write("[]")


def run():
    args = parser.parse_args()

    if args.action == "collect":
        collect(args.collect_from, args.save_to)
        exit(0)


if __name__ == "__main__":
    run()
