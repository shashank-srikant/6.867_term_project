"use strict";
const ts = require('typescript');
const fs = require('fs');
const path = require('path');

let removableLexicalKinds = [
    ts.SyntaxKind.EndOfFileToken,
    ts.SyntaxKind.NewLineTrivia,
    ts.SyntaxKind.WhitespaceTrivia
];

function walkSync(dir, filelist) {
    fs.readdirSync(dir).forEach(function (file) {
        let fullPath = path.join(dir, file);
        try {
            if (fs.statSync(fullPath).isDirectory()) {
		if (file != ".git")
		    walkSync(dir + '/' + file, filelist);
            } else if (file.endsWith('.js') || file.endsWith('.ts')) {
                if (fs.statSync(fullPath).size < 1*1000*1000)
		    filelist.push(fullPath);
            }
        }
        catch (e) {
            console.error("Error processing " + file);
        }
    });
}

function mkdirSync(dir) {
    var cumulative = dir.startsWith('/') ? '/' : '';
    for (let split of dir.split(path.sep)) {
	cumulative = path.join(cumulative, split);
	if (cumulative && !fs.existsSync(cumulative)) {
	    fs.mkdirSync(cumulative);
	}
    }
}

function extractTree(tree, checker) {
    if (removableLexicalKinds.indexOf(tree.kind) != -1 || ts.SyntaxKind[tree.kind].indexOf("JSDoc") != -1) {
        return null;
    }
    let children = tree.getChildren().map(c => extractTree(c, checker)).filter(x =>  x != null);

    var syntax = tree.getText();

    if (syntax.length === 0) {
	return null;
    }

    var type;

    let symbol = checker.getSymbolAtLocation(tree);
    if (!symbol) {
	type = "$any$"
    } else {
	let mType = checker.typeToString(checker.getTypeOfSymbolAtLocation(symbol, tree));
	if (checker.isUnknownSymbol(symbol) || mType.startsWith('typeof ')) {
	    type = '$any$';
	} else if (
	    mType.startsWith('"') || mType.match('[0-9]+')
	) {
	    type = "O";
	} else {
	    type = '$' + mType + '$';
	}
    }

    if (children.length > 0) {
	syntax = '$complex$';
    }

    return {
	syntax: syntax,
	kind: tree.kind,
	type: type,
	children: children
    }
}

function processProject(srcDir, destDir) {
    let files = [];
    walkSync(srcDir, files);

    let program = ts.createProgram(files, { target: ts.ScriptTarget.Latest, module: ts.ModuleKind.CommonJS, checkJs: true, allowJs: true });
    let checker = null;
    try {
	checker = program.getTypeChecker();
    }
    catch (err) {
	console.log(`Failed to process project ${srcDir}`);
	return
    }

    program.getSourceFiles().forEach(sourceFile => {
        let filename = sourceFile.getSourceFile().fileName;
	filename = path.relative(srcDir, filename);

        if (filename.endsWith('.d.ts')) return;
        if (filename.startsWith("..")) return;

        let tree = extractTree(sourceFile, checker);
	if (tree === null) {
	    return;
	}

	let filenameParse = path.parse(filename);
	let dirname = path.join(destDir, filenameParse.dir);
	filename = path.join(dirname, filenameParse.name + '.json');

	try {
	    mkdirSync(dirname);
	} catch (err) {
	    console.log(`Could not mkdir ${dirname}: ${err}`);

	}

	fs.writeFileSync(filename, JSON.stringify(tree));
    });
}

function processDir(srcDir, destDir) {
    let children = fs.readdirSync(srcDir, { withFileTypes: true });

    if (children.find(value =>  value.name === 'tsconfig.json')) {
	processProject(srcDir, destDir);
    } else {
	children.forEach(f =>  {
	    let srcF = path.join(srcDir, f.name);
	    let destF = path.join(destDir, f.name);

	    let isBadDirectory = (
		f.name.indexOf('DefinitelyTyped') > -1
		    || srcF.indexOf('TypeScript/tests') > -1
		    || f.name == '.git'
	    );

	    if (f.isDirectory() && isBadDirectory) {
		return;
	    }

	    if (f.isDirectory()) {
		processDir(srcF, destF);
	    }
	});
    }
}

function main() {
    if (process.argv.length < 4) {
	console.log('Expected 2 arguments: [source dir], where to read the TypeScript files from, and [dest dir], where to write parsed ASTs to');
	process.exit(1);
    }

    let srcDir = process.argv[2];
    let destDir = process.argv[3];

    if (!fs.existsSync(srcDir)) {
	console.log(`Source directory ${srcDir} doesn't exist!`);
	process.exit(1);
    }

    processDir(srcDir, destDir);
}

if (require.main === module) {
    main();
}
