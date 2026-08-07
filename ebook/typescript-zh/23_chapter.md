# 第 23 章：在 TypeScript 中使用 RequireJS

RequireJS 是一个 JavaScript 文件和模块加载器。它针对浏览器内使用进行了优化，但也可以在其他 JavaScript 环境中使用，如 Rhino 和 Node。使用像 RequireJS 这样的模块化脚本加载器可以提高代码的速度和质量。

在 TypeScript 中使用 RequireJS 需要配置 `tsconfig.json`，并在任何 HTML 文件中包含一段代码片段。编译器会将导入语法从 TypeScript 语法转换为 RequireJS 的格式。

## 第 23.1 节：使用 RequireJS CDN 包含已编译的 TypeScript 文件的 HTML 示例

```html
<body onload="__init();">
  ...
  <script src="http://requirejs.org/docs/release/2.3.2/comments/require.js"></script>
  <script>
    function __init() {
      require(["view/index.js"]);
    }
  </script>
</body>
```

## 第 23.2 节：使用 RequireJS 导入风格编译到 view 文件夹的 tsconfig.json 示例

```json
{
  "module": "amd",    // 使用 AMD 模块代码生成器，可与 RequireJS 配合使用
  "rootDir": "./src", // 将此更改为你的源文件夹
  "outDir": "./view",
  ...
}
```
