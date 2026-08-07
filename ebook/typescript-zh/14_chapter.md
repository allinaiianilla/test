第 14 章：导入外部库

第 14.1 节：查找定义文件

对于 TypeScript 2.x：来自 DefinitelyTyped 的类型定义可通过 @types npm 包获取：

```
npm i --save lodash
npm i --save-dev @types/lodash
```

但如果你想使用来自其他仓库的类型，也可以使用旧的方式：

对于 TypeScript 1.x：Typings 是一个 npm 包，可以自动将类型定义文件安装到本地项目中。建议你阅读其快速入门指南。

```
npm install -global typings
```

现在我们有了 typings 命令行工具。第一步是搜索项目中使用的包：

```
typings search lodash
NAME              SOURCE HOMEPAGE                                        DESCRIPTION VERSIONS UPDATED
lodash            dt     http://lodash.com/                                          2        2016-07-20T00:13:09.000Z
lodash            global                                                           1        2016-07-01T20:51:07.000Z
lodash            npm    https://www.npmjs.com/package/lodash                       1        2016-07-01T20:51:07.000Z
```

然后决定从哪个源安装。我使用 dt，它代表 DefinitelyTyped——一个社区可以编辑类型定义的 GitHub 仓库，通常也是更新最及时的。

安装类型定义文件：

```
typings install dt~lodash --global --save
```

让我们分解最后一条命令。我们将 lodash 的 DefinitelyTyped 版本作为全局类型定义文件安装到项目中，并将其作为依赖保存到 `typings.json` 中。现在，无论在哪里导入 lodash，TypeScript 都会加载 lodash 的类型定义文件。

如果只想安装仅在开发环境下使用的类型定义，可以添加 `--save-dev` 标志：

```
typings install chai --save-dev
```

第 14.2 节：从 npm 导入模块

如果你有该模块的类型定义文件（d.ts），可以使用 `import` 语句：

```typescript
import _ = require('lodash');
```

如果没有该模块的定义文件，TypeScript 将在编译时抛出错误，因为它找不到你要导入的模块。在这种情况下，你可以使用普通的运行时 `require` 函数导入模块，不过这将返回 `any` 类型：

```typescript
// 变量 _ 的类型为 any，因此 TypeScript 不会执行任何类型检查。
const _: any = require('lodash');
```

从 TypeScript 2.0 开始，你也可以使用简写环境模块声明，以便在没有类型定义文件时告知 TypeScript 某个模块存在。不过在这种情况下，TypeScript 无法提供任何有意义的类型检查。

```typescript
declare module "lodash";

// 现在你可以以任何方式从 lodash 导入：
import { flatten } from "lodash";
import * as _ from "lodash";
```

从 TypeScript 2.1 开始，规则进一步放宽。现在，只要模块存在于你的 `node_modules` 目录中，即使没有任何模块声明，TypeScript 也会允许你导入它。（请注意，如果使用 `--noImplicitAny` 编译选项，以下代码仍会生成警告。）

```typescript
// 如果 `node_modules/someModule/index.js` 存在，或 `node_modules/someModule/package.json` 中有有效的 "main" 入口，即可正常工作
import { foo } from "someModule";
```

第 14.3 节：使用没有类型定义的全局外部库

虽然模块是理想选择，但如果使用的库是通过全局变量（如 `$` 或 `_`）引用的（因为它通过 `script` 标签加载），你可以创建一个环境声明来引用它：

```typescript
declare const _: any;
```

第 14.4 节：使用 TypeScript 2.x 查找定义文件

在 TypeScript 2.x 版本中，类型定义可从 npm 的 @types 仓库获取。TypeScript 编译器会自动解析这些定义，使用起来也更简单。要安装类型定义，只需将其作为项目 package.json 中的开发依赖安装即可：

```
npm i -S lodash
npm i -D @types/lodash
```

安装后，像以前一样直接使用该模块即可：

```typescript
import * as _ from 'lodash'
```
