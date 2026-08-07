# 第 25 章：TypeScript 与 SystemJS

## 第 25.1 节：在浏览器中使用 SystemJS 的 Hello World

### 安装 systemjs 和 plugin-typescript

```bash
npm install systemjs
npm install plugin-typescript
```

**注意：** 这将安装 TypeScript 2.0.0 编译器，该版本尚未发布。对于 TypeScript 1.8，你必须使用 plugin-typescript 4.0.16。

### 创建 `hello.ts` 文件

```typescript
export function greeter(person: String) {
  return 'Hello, ' + person;
}
```

### 创建 `hello.html` 文件

```html
<!doctype html>
<html>
<head>
  <title>Hello World in TypeScript</title>
  <script src="node_modules/systemjs/dist/system.src.js"></script>
  <script src="config.js"></script>
  <script>
    window.addEventListener('load', function() {
      System.import('./hello.ts').then(function(hello) {
        document.body.innerHTML = hello.greeter('World');
      });
    });
  </script>
</head>
<body>
</body>
</html>
```

### 创建 `config.js` - SystemJS 配置文件

```javascript
System.config({
  packages: {
    "plugin-typescript": {
      "main": "plugin.js"
    },
    "typescript": {
      "main": "lib/typescript.js",
      "meta": {
        "lib/typescript.js": {
          "exports": "ts"
        }
      }
    }
  },
  map: {
    "plugin-typescript": "node_modules/plugin-typescript/lib/",
    /* 注意：这适用于 npm 3（node 6） */
    /* 对于 npm 2，typescript 路径将是 */
    /* node_modules/plugin-typescript/node_modules/typescript */
    "typescript": "node_modules/typescript/"
  },
  transpiler: "plugin-typescript",
  meta: {
    "./hello.ts": {
      format: "esm",
      loader: "plugin-typescript"
    }
  },
  typescriptOptions: {
    typeCheck: 'strict'
  }
});
```

**注意：** 如果你不需要类型检查，请从 `config.js` 中移除 `loader: "plugin-typescript"` 和 `typescriptOptions`。另请注意，它永远不会检查 JavaScript 代码，特别是在 HTML 示例中 `<script>` 标签内的代码。

### 测试

```bash
npm install live-server
./node_modules/.bin/live-server --open=hello.html
```

### 为生产环境构建

```bash
npm install systemjs-builder
```

### 创建 `build.js` 文件：

```javascript
var Builder = require('systemjs-builder');
var builder = new Builder();

builder.loadConfig('./config.js').then(function() {
  builder.bundle('./hello.ts', './hello.js', {minify: true});
});
```

### 从 hello.ts 构建 hello.js

```bash
node build.js
```

### 在生产环境中使用

只需在首次使用之前通过 script 标签加载 hello.js。

### `hello-production.html` 文件：

```html
<!doctype html>
<html>
<head>
  <title>Hello World in TypeScript</title>
  <script src="node_modules/systemjs/dist/system.src.js"></script>
  <script src="config.js"></script>
  <script src="hello.js"></script>
  <script>
    window.addEventListener('load', function() {
      System.import('./hello.ts').then(function(hello) {
        document.body.innerHTML = hello.greeter('World');
      });
    });
  </script>
</head>
<body>
</body>
</html>
```
