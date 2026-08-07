第 17 章：在 webpack 中使用 TypeScript

第 17.1 节：webpack.config.js

安装 loader：

```
npm install --save-dev ts-loader source-map-loader
```

tsconfig.json

```json
{
  "compilerOptions": {
    "sourceMap": true,
    "noImplicitAny": true,
    "module": "commonjs",
    "target": "es5",
    "jsx": "react"    // 如果你想使用 React JSX
  }
}
```

```javascript
module.exports = {
    entry: "./src/index.ts",
    output: {
        filename: "./dist/bundle.js",
    },

    // 启用 sourcemap 以便调试 webpack 的输出。
    devtool: "source-map",

    resolve: {
        // 添加 '.ts' 和 '.tsx' 作为可解析的扩展名。
        extensions: ["", ".webpack.js", ".web.js", ".ts", ".tsx", ".js"]
    },

    module: {
        loaders: [
            // 所有扩展名为 '.ts' 或 '.tsx' 的文件将由 'ts-loader' 处理。
            { test: /\.tsx?$/, loader: "ts-loader" }
        ],

        preLoaders: [
            // 所有输出的 '.js' 文件将由 'source-map-loader' 重新处理 sourcemap。
            { test: /\.js$/, loader: "source-map-loader" }
        ]
    },

    /*****************************
     *   如果你想使用 React      *
     ****************************/
    // 当导入一个路径匹配以下模式的模块时，直接
    // 假定存在对应的全局变量并使用它。
    // 这很重要，因为它允许我们避免打包所有的
    // 依赖项，使得浏览器可以在构建之间缓存这些库。
    // externals: {
    //     "react": "React",
    //     "react-dom": "ReactDOM"
    // },
};
```
