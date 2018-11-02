## Setup
- Preferably, install `nvm` to manage `npm` related tools (https://github.com/creationix/nvm)
- `package-lock.json` lists out the dependencies.
    - run `npm install typescript`
    - run `npm install @types/node`

## `typescript.Node` documentation
Our savior! Provides documentation for the interfaces in `Node` class of `typescript` module.

http://ts2jsdoc.js.org/typescript/ts.Node.html

http://ts2jsdoc.js.org/typescript/ts.html

`Pro-tip` Install `Visual Studio Code`. Its auto-complete feature helps learning about methods and properties of the `Node` class.

## Sample AST (JSON-ized)
```
SourceFileObject {
  pos: 0,
  end: 2192,
  flags: 0,
  transformFlags: undefined,
  parent: undefined,
  kind: 277,
  text:
   'import { Injectable } .... }',
  bindDiagnostics: [],
  bindSuggestionDiagnostics: undefined,
  languageVersion: 6,
  fileName: '../../data/test/facebook.ts',
  languageVariant: 0,
  isDeclarationFile: false,
  ...
  hasNoDefaultLib: false,
  statements:
   [ NodeObject {
       pos: 0,
       end: 44,
       flags: 0,
       transformFlags: undefined,
       parent: [Circular],
       kind: 247,
       decorators: undefined,
       modifiers: undefined,
       importClause: [NodeObject],
       moduleSpecifier: [TokenObject],
       modifierFlagsCache: 536870912 },
     NodeObject {
       pos: 44,
       end: 101,
       flags: 0,
       transformFlags: undefined,
       parent: [Circular],
       kind: 247,
       decorators: undefined,
       modifiers: undefined,
       importClause: [NodeObject],
       moduleSpecifier: [TokenObject] },
     NodeObject {
       pos: 101,
       end: 154,
       flags: 0,
       transformFlags: undefined,
       parent: [Circular],
       kind: 247,
       decorators: undefined,
       modifiers: undefined,
       importClause: [NodeObject],
       moduleSpecifier: [TokenObject] },
     NodeObject {
       pos: 154,
       end: 211,
       flags: 0,
       transformFlags: undefined,
       parent: [Circular],
       kind: 247,
       decorators: undefined,
       modifiers: undefined,
       importClause: [NodeObject],
       moduleSpecifier: [TokenObject] },
     NodeObject {
       pos: 211,
       end: 270,
       flags: 0,
       transformFlags: undefined,
       parent: [Circular],
       kind: 247,
       decorators: undefined,
       modifiers: undefined,
       importClause: [NodeObject],
       moduleSpecifier: [TokenObject] },
     NodeObject {
       pos: 270,
       end: 325,
       flags: 0,
       transformFlags: undefined,
       parent: [Circular],
       kind: 247,
       decorators: undefined,
       modifiers: undefined,
       importClause: [NodeObject],
       moduleSpecifier: [TokenObject] },
       ...
     ,
     pos: 0,
     end: 2192 ],
  endOfFileToken:
   TokenObject { pos: 2192, end: 2192, flags: 32768, parent: [Circular], kind: 1 },
  externalModuleIndicator:
   NodeObject {
     pos: 0,
     end: 44,
     flags: 0,
     transformFlags: undefined,
     parent: [Circular],
     kind: 247,
     decorators: undefined,
     modifiers: undefined,
     importClause:
      NodeObject {
        pos: 6,
        end: 21,
        flags: 0,
        transformFlags: undefined,
        parent: [Circular],
        kind: 248,
        namedBindings: [NodeObject] },
     moduleSpecifier:
      TokenObject {
        pos: 26,
        end: 42,
        flags: 0,
        parent: [Circular],
        kind: 9,
        text: '@angular/core' },
     modifierFlagsCache: 536870912 },
  nodeCount: 459,
  identifierCount: 141,
  identifiers:
   Map {
     'Injectable' => 'Injectable',
     '@angular/core' => '@angular/core',
     'AuthResponse' => 'AuthResponse',
     '../models/auth-response' => '../models/auth-response',
     'InitParams' => 'InitParams',
     '../models/init-params' => '../models/init-params',
     'LoginOptions' => 'LoginOptions',
     '../models/login-options' => '../models/login-options',
     'LoginResponse' => 'LoginResponse',
     '../models/login-response' => '../models/login-response',
     'LoginStatus' => 'LoginStatus',
     ...
     },
  parseDiagnostics:
   [ { file: [Circular],
       start: 561,
       length: 1,
       messageText: '\'{\' or \';\' expected.',
       category: 1,
       code: 1144,
       reportsUnnecessary: undefined },
     { file: [Circular],
       start: 575,
       length: 1,
       messageText: '\':\' expected.',
       category: 1,
       code: 1005,
       reportsUnnecessary: undefined },
     ...
     { file: [Circular],
       start: 2191,
       length: 1,
       messageText: 'Declaration or statement expected.',
       category: 1,
       code: 1128,
       reportsUnnecessary: undefined } ] 
}
```