import {ArgumentParser} from 'argparse';
import common = require('common-prefix');
import {EdgeAST} from "./edge_ast";
import {EdgeUseDef} from "./edge_use_def";
import * as fs from 'fs';
import {Graph} from "./graph";
import * as path from 'path';
import shell = require('shelljs');
import {map2obj, print_obj} from "./utils";

function processDir(dir: string, common_prefix_dir: string, dest: string) {
    for (let entry of fs.readdirSync(dir, {withFileTypes: true})) {
        if (entry.isDirectory()) {
            processDir(path.join(dir, entry.name), common_prefix_dir, dest);
        } else {
            processFile(path.join(dir, entry.name), common_prefix_dir, dest);
        }
    }
}

function processFile(file: string, common_prefix_dir: string, dest: string) {
    let file_path = path.parse(path.relative(common_prefix_dir, file));
    if (file_path.ext !== '.ts') {
	    return;
    }
    let output_file_path = path.join(file_path.dir, file_path.name + '.json');

    var graph_obj = new Graph(file);
    let edge_obj_list = []
    edge_obj_list.push(new EdgeAST());
    edge_obj_list.push(new EdgeUseDef());
    let [node_id_to_nodekind_map, edge_list, labels_list, label_dict] = graph_obj.ast2graph(edge_obj_list);

    shell.mkdir('-p', path.join(dest, file_path.dir));

    print_obj({
	"nodes": node_id_to_nodekind_map,
	"edges": edge_list,
	"labels": labels_list,
	"label_map": map2obj(label_dict)
    }, dest, output_file_path);
}

function get_common_directory(paths: string[]) : string {
    if (paths.length === 0) {
	throw new Error('Expected some paths, got none!');
    }
    let common_prefix = common(paths);
    if (fs.existsSync(common_prefix) &&
	fs.statSync(common_prefix).isDirectory()) {
	return common_prefix;
    } else {
	return path.parse(common_prefix).dir;
    }
}

function main() {
    let parser = new ArgumentParser({
	addHelp: true,
	description: 'Process all ASTs in each [file_or_dir], saving them with a directory structure relative to their common root in [dest]',
    });

    parser.addArgument(
	['file_or_dir'],
	{
	    nargs: '+',
	    help: 'Programs to process',
	}
    )

    parser.addArgument(
	['dest'],
	{
	    help: 'Destination root',
	}
    )

    let args = parser.parseArgs();

    let src_files: string[] = args.file_or_dir.map((f: string) => path.resolve('.', f));
    let common_prefix_dir = get_common_directory(src_files);
    let src_files_stats: fs.Stats[] = src_files.map(fs.statSync);

    for (let idx in src_files) {
	let src_file = src_files[idx];
	let src_file_stats = src_files_stats[idx];

	if (src_file_stats.isDirectory()) {
	    processDir(src_file, common_prefix_dir, args.dest);
	} else {
	    processFile(src_file, common_prefix_dir, args.dest);
	}
    }
}

if (require.main === module) {
    main();
}
