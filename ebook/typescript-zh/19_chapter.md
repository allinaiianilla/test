第 19 章：在没有类型定义文件时如何使用 JavaScript 库

虽然一些现有的 JavaScript 库有类型定义文件，但仍有许多没有。TypeScript 提供了几种处理缺失声明的模式。

第 19.1 节：创建一个导出默认 any 的模块

对于更复杂的项目，或者在需要逐步为某个依赖添加类型的情况下，创建一个模块可能是更清晰的方式。以 jQuery 为例（尽管它确实有类型定义可用）：

```typescript
// 放在 jquery.d.ts 中
declare let $: any;
export default $;
```

然后在项目的任何文件中，可以这样导入此定义：

```typescript
// 其他 .ts 文件
import $ from "jquery";
```

导入后，`$` 的类型为 `any`。

如果该库有多个顶层变量，可以使用命名导出和导入：

```typescript
// 放在 jquery.d.ts 中
declare module "jquery" {
    let $: any;
    let jQuery: any;

    export { $ };
    export { jQuery };
}
```

然后可以导入并使用这两个名称：

```typescript
// 其他 .ts 文件
import { $, jQuery } from "jquery";
$.doThing();
jQuery.doOtherThing();
```

第 19.2 节：声明一个 any 全局变量

有时最简单的方式是直接声明一个类型为 `any` 的全局变量，尤其是在简单项目中。如果 jQuery 没有类型声明（实际上它有），可以这样写：

```typescript
declare var $: any;
```

现在任何对 `$` 的使用都将被类型化为 `any`。

第 19.3 节：使用环境模块

如果你只想像表明导入的意图（而不想声明全局变量），但又不想处理任何显式的定义，可以导入一个环境模块。

```typescript
// 在声明文件中（如 declarations.d.ts）
declare module "jquery";  // 注意这里没有定义任何导出内容
```

然后你可以从环境模块导入：

```typescript
// 其他 .ts 文件
import { $, jQuery } from "jquery";
```

从已声明模块导入的任何内容（如上面的 `$` 和 `jQuery`）都将为 `any` 类型。
