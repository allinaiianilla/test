# 第 28 章：tsconfig.json

## 第 28.1 节：使用 tsconfig.json 创建 TypeScript 项目

`tsconfig.json` 文件的存在表明当前目录是启用了 TypeScript 的项目的根目录。初始化 TypeScript 项目，或者更准确地说是创建 `tsconfig.json` 文件，可以通过以下命令完成：

```bash
tsc --init
```

从 TypeScript v2.3.0 及更高版本开始，这将默认创建以下 `tsconfig.json`：

```json
{
  "compilerOptions": {
    /* 基本选项 */
    "target": "es5",      /* 指定 ECMAScript 目标版本：'ES3'（默认）、'ES5'、'ES2015'、'ES2016'、'ES2017' 或 'ESNEXT'。 */
    "module": "commonjs", /* 指定模块代码生成：'commonjs'、'amd'、'system'、'umd' 或 'es2015'。 */
    // "lib": [],                            /* 指定编译中包含的库文件： */
    // "allowJs": true,                      /* 允许编译 JavaScript 文件。 */
    // "checkJs": true,                      /* 报告 .js 文件中的错误。 */
    // "jsx": "preserve",                    /* 指定 JSX 代码生成：'preserve'、'react-native' 或 'react'。 */
    // "declaration": true,                  /* 生成相应的 '.d.ts' 文件。 */
    // "sourceMap": true,                    /* 生成相应的 '.map' 文件。 */
    // "outFile": "./",                      /* 将输出合并并输出到单个文件。 */
    // "outDir": "./",                       /* 将输出结构重定向到该目录。 */
    // "rootDir": "./",                      /* 指定输入文件的根目录。用于通过 --outDir 控制输出目录结构。 */
    // "removeComments": true,               /* 不在输出中生成注释。 */
    // "noEmit": true,                       /* 不生成输出。 */
    // "importHelpers": true,                /* 从 'tslib' 导入辅助函数。 */
    // "downlevelIteration": true,           /* 在目标为 'ES5' 或 'ES3' 时，为 'for-of'、展开和解构中的可迭代对象提供完整支持。 */
    // "isolatedModules": true,              /* 将每个文件作为单独的模块转译（类似于 'ts.transpileModule'）。 */

    /* 严格类型检查选项 */
    "strict": true      /* 启用所有严格的类型检查选项。 */
    // "noImplicitAny": true,                /* 对具有隐含 'any' 类型的表达式和声明报错。 */
    // "strictNullChecks": true,             /* 启用严格的 null 检查。 */
    // "noImplicitThis": true,               /* 对具有隐含 'any' 类型的 'this' 表达式报错。 */
    // "alwaysStrict": true,                 /* 以严格模式解析，并为每个源文件生成 "use strict"。 */

    /* 额外检查 */
    // "noUnusedLocals": true,               /* 报告未使用的局部变量错误。 */
    // "noUnusedParameters": true,           /* 报告未使用的参数错误。 */
    // "noImplicitReturns": true,            /* 当并非函数中的所有代码路径都返回值时报告错误。 */
    // "noFallthroughCasesInSwitch": true,   /* 报告 switch 语句中 fallthrough 情况的错误。 */

    /* 模块解析选项 */
    // "moduleResolution": "node",           /* 指定模块解析策略：'node'（Node.js）或 'classic'（TypeScript 1.6 之前）。 */
    // "baseUrl": "./",                      /* 解析非绝对模块名称的基础目录。 */
    // "paths": {},                          /* 一系列映射导入到相对于 'baseUrl' 的查找位置的条目。 */
    // "rootDirs": [],                       /* 根文件夹列表，其组合内容代表项目在运行时的结构。 */
    // "typeRoots": [],                      /* 要包含类型定义的文件夹列表。 */
    // "types": [],                          /* 编译中包含的类型声明文件。 */
    // "allowSyntheticDefaultImports": true, /* 允许从没有默认导出的模块进行默认导入。这不影响代码生成，仅影响类型检查。 */

    /* Source Map 选项 */
    // "sourceRoot": "./",                   /* 指定调试器应定位 TypeScript 文件的位置，而不是源位置。 */
    // "mapRoot": "./",                      /* 指定调试器应定位 map 文件的位置，而不是生成的位置。 */
    // "inlineSourceMap": true,              /* 生成包含 source maps 的单个文件，而不是单独的文件。 */
    // "inlineSources": true,                /* 将源代码与 sourcemaps 一起生成在单个文件中；需要设置 '--inlineSourceMap' 或 '--sourceMap'。 */

    /* 实验性选项 */
    // "experimentalDecorators": true,       /* 启用对 ES7 装饰器的实验性支持。 */
    // "emitDecoratorMetadata": true,        /* 启用为装饰器生成类型元数据的实验性支持。 */
  }
}
```

大多数（如果不是全部）选项都会自动生成，只有必需的基本选项保持未注释状态。

旧版本的 TypeScript，例如 v2.0.x 及更低版本，会生成如下 `tsconfig.json`：

```json
{
  "compilerOptions": {
    "module": "commonjs",
    "target": "es5",
    "noImplicitAny": false,
    "sourceMap": false
  }
}
```

## 第 28.2 节：减少编程错误的配置

有一些非常好的配置可以强制类型检查并获得更多有用的错误信息，这些默认情况下并未激活。

```json
{
  "compilerOptions": {
    "alwaysStrict": true,      // 以严格模式解析，并为每个源文件生成 "use strict"。

    // 如果你在引用的文件中使用了错误的大小写，例如文件名是 Global.ts 而你使用
    // /// <reference path="global.ts" /> 来引用此文件，这可能会导致意外的错误。
    // 参见：http://stackoverflow.com/questions/36628612/typescript-transpiler-casing-issue
    "forceConsistentCasingInFileNames": true,  // 禁止对同一文件使用大小写不一致的引用。

    // "allowUnreachableCode": false,    // 不报告无法访问的代码错误。（默认：False）
    // "allowUnusedLabels": false,       // 不报告未使用的标签错误。（默认：False）

    "noFallthroughCasesInSwitch": true,  // 报告 switch 语句中 fall through 情况的错误。
    "noImplicitReturns": true,           // 当并非函数中的所有代码路径都返回值时报告错误。
    "noUnusedParameters": true,          // 报告未使用的参数错误。
    "noUnusedLocals": true,              // 报告未使用的局部变量错误。
    "noImplicitAny": true,               // 对具有隐含 "any" 类型的表达式和声明报错。
    "noImplicitThis": true,              // 对具有隐含 "any" 类型的 this 表达式报错。
    "strictNullChecks": true,            // null 和 undefined 值不在每种类型的域中，只能赋值给它们自身和 any。

    // 要强制执行这些规则，请添加此配置。
    "noEmitOnError": true                // 如果报告了任何错误，则不生成输出。
  }
}
```

还不够？如果你是一个严格的程序员，想要更多，那么你可能会对在通过 tsc 编译之前使用 tslint 检查你的 TypeScript 文件感兴趣。查看如何配置 tslint 以实现更严格的代码检查。

## 第 28.3 节：compileOnSave

设置顶级属性 `compileOnSave` 可以在保存时向 IDE 发出信号，为给定的 `tsconfig.json` 生成所有文件。

```json
{
  "compileOnSave": true,
  "compilerOptions": { ... },
  "exclude": [ ... ]
}
```

此功能从 TypeScript 1.8.4 及更高版本开始可用，但需要 IDE 直接支持。目前，支持的 IDE 示例包括：

- Visual Studio 2015（带 Update 3）
- JetBrains WebStorm
- Atom（带 atom-typescript）

## 第 28.4 节：注释

`tsconfig.json` 文件可以包含行注释和块注释，使用与 ECMAScript 相同的规则。

```json
// 前导注释
{
  "compilerOptions": {
    // 这是一个行注释
    "module": "commonjs", // 行尾注释
    "target" /* 内联块注释 */ : "es5",
    /* 这是一个块注释 */
  }
}
/* 尾随注释 */
```

## 第 28.5 节：preserveConstEnums

TypeScript 支持通过 `const enum` 声明的常量枚举。这通常只是语法糖，因为常量枚举会在编译后的 JavaScript 中被内联。例如，以下代码：

```typescript
const enum Tristate { True, False, Unknown }

var something = Tristate.True;
```

编译为：

```javascript
var something = 0;
```

尽管内联带来了性能优势，你可能更希望保留枚举，即使是常量枚举（例如：你可能希望在开发代码中保持可读性）。要实现这一点，你必须在 `tsconfig.json` 中将 `compilerOptions` 中的 `preserveConstEnums` 子句设置为 `true`。

```json
{
  "compilerOptions": {
    "preserveConstEnums" = true,
    ...
  },
  "exclude": [ ... ]
}
```

通过这种方式，前面的示例将像其他枚举一样被编译，如下面的代码片段所示。

```javascript
var Tristate;
(function (Tristate) {
  Tristate[Tristate["True"] = 0] = "True";
  Tristate[Tristate["False"] = 1] = "False";
  Tristate[Tristate["Unknown"] = 2] = "Unknown";
})(Tristate || (Tristate = {}));

var something = Tristate.True
```
