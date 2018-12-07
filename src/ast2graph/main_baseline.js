"use strict";
exports.__esModule = true;
var argparse_1 = require("argparse");
var common = require("common-prefix");
var fs = require("fs");
var graph_1 = require("./graph");
var path = require("path");
var edge_features_1 = require("./edge_features");
function processDir(dir, common_prefix_dir, dest) {
    for (var _i = 0, _a = fs.readdirSync(dir, { withFileTypes: true }); _i < _a.length; _i++) {
        var entry = _a[_i];
        if (entry.isDirectory()) {
            processDir(path.join(dir, entry.name), common_prefix_dir, dest);
        }
        else {
            processFile(path.join(dir, entry.name), common_prefix_dir, dest);
        }
    }
}
function processFile(file, common_prefix_dir, dest) {
    var file_path = path.parse(path.relative(common_prefix_dir, file));
    if (file_path.ext !== '.ts') {
        return;
    }
    var output_file_path = path.join(file_path.dir, file_path.name + '.json');
    var graph_obj = new graph_1.Graph(file);
    var edge_obj = new edge_features_1.EdgeFeatures();
    graph_obj.ast2feature(edge_obj);
}
function get_common_directory(paths) {
    if (paths.length === 0) {
        throw new Error('Expected some paths, got none!');
    }
    var common_prefix = common(paths);
    if (fs.existsSync(common_prefix) &&
        fs.statSync(common_prefix).isDirectory()) {
        return common_prefix;
    }
    else {
        return path.parse(common_prefix).dir;
    }
}
function main() {
    var parser = new argparse_1.ArgumentParser({
        addHelp: true,
        description: 'Process all ASTs in each [file_or_dir], saving them with a directory structure relative to their common root in [dest]'
    });
    parser.addArgument(['file_or_dir'], {
        nargs: '+',
        help: 'Programs to process'
    });
    parser.addArgument(['dest'], {
        help: 'Destination root'
    });
    var args = parser.parseArgs();
    var src_files = args.file_or_dir.map(function (f) { return path.resolve('.', f); });
    var common_prefix_dir = get_common_directory(src_files);
    var src_files_stats = src_files.map(fs.statSync);
    for (var idx in src_files) {
        var src_file = src_files[idx];
        var src_file_stats = src_files_stats[idx];
        if (src_file_stats.isDirectory()) {
            processDir(src_file, common_prefix_dir, args.dest);
        }
        else {
            processFile(src_file, common_prefix_dir, args.dest);
        }
    }
}
if (require.main === module) {
    main();
}
