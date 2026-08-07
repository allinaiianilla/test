# 第 26 章：在 TypeScript 中使用 React（JS 和原生）

## 第 26.1 节：使用 TypeScript 编写的 ReactJS 组件

你可以轻松地在 TypeScript 中使用 ReactJS 的组件。只需将 `jsx` 文件扩展名重命名为 `tsx`：

```tsx
//helloMessage.tsx:
var HelloMessage = React.createClass({
  render: function() {
    return <div>Hello {this.props.name}</div>;
  }
});

ReactDOM.render(<HelloMessage name="John" />, mountNode);
```

但是，为了充分利用 TypeScript 的主要特性（静态类型检查），你必须做几件事：

**1) 将 React.createClass 转换为 ES6 类：**

```tsx
//helloMessage.tsx:
class HelloMessage extends React.Component {
  render() {
    return <div>Hello {this.props.name}</div>;
  }
}

ReactDOM.render(<HelloMessage name="John" />, mountNode);
```

关于转换为 ES6 的更多信息，请查看此处。

**2) 添加 Props 和 State 接口：**

```tsx
interface Props {
  name: string;
  optionalParam?: number;
}

interface State {
  // 在我们的例子中为空
}

class HelloMessage extends React.Component<Props, State> {
  render() {
    return <div>Hello {this.props.name}</div>;
  }
}

// TypeScript 将允许你在不传递可选参数的情况下创建组件
ReactDOM.render(<HelloMessage name="Sebastian" />, mountNode);

// 但如果你传递了错误类型的可选参数，它确实会进行检查
ReactDOM.render(<HelloMessage name="Sebastian" optionalParam='foo' />, mountNode);
```

现在，如果开发者忘记传递 props，或者试图传递接口中未定义的 props，TypeScript 将显示错误。

## 第 26.2 节：TypeScript & React & Webpack

### 全局安装 typescript、typings 和 webpack

```bash
npm install -g typescript typings webpack
```

### 安装 loader 并链接 typescript

```bash
npm install --save-dev ts-loader source-map-loader
npm link typescript
```

链接 TypeScript 允许 ts-loader 使用你全局安装的 TypeScript，而不需要单独的本地副本（TypeScript 文档）。

### 使用 TypeScript 2.x 安装 `.d.ts` 文件

```bash
npm i @types/react --save-dev
npm i @types/react-dom --save-dev
```

### 使用 TypeScript 1.x 安装 `.d.ts` 文件

```bash
typings install --global --save dt~react
typings install --global --save dt~react-dom
```

### `tsconfig.json` 配置文件

```json
{
  "compilerOptions": {
    "sourceMap": true,
    "noImplicitAny": true,
    "module": "commonjs",
    "target": "es5",
    "jsx": "react"
  }
}
```

### `webpack.config.js` 配置文件

```javascript
module.exports = {
  entry: "<path to entry point>", // 例如 ./src/helloMessage.tsx
  output: {
    filename: "<path to bundle file>", // 例如 ./dist/bundle.js
  },

  // 为调试 webpack 的输出启用 sourcemaps。
  devtool: "source-map",

  resolve: {
    // 添加 '.ts' 和 '.tsx' 作为可解析的扩展名。
    extensions: ["", ".webpack.js", ".web.js", ".ts", ".tsx", ".js"]
  },

  module: {
    loaders: [
      // 所有带有 '.ts' 或 '.tsx' 扩展名的文件将由 'ts-loader' 处理。
      { test: /\.tsx?$/, loader: "ts-loader" }
    ],

    preLoaders: [
      // 所有输出的 '.js' 文件将由 'source-map-loader' 重新处理其 sourcemaps。
      { test: /\.js$/, loader: "source-map-loader" }
    ]
  },

  // 当导入的模块路径匹配以下之一时，只需
  // 假设存在相应的全局变量并使用它。
  // 这很重要，因为它允许我们避免打包所有
  // 依赖项，从而使浏览器能够在构建之间缓存这些库。
  externals: {
    "react": "React",
    "react-dom": "ReactDOM"
  },
};
```

最后运行 `webpack` 或 `webpack -w`（用于监视模式）。

**注意：** React 和 ReactDOM 被标记为外部依赖。
