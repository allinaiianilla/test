# 第 22 章：与构建工具集成

## 第 22.1 节：Browserify

### 安装

```bash
npm install tsify
```

### 使用命令行界面

```bash
browserify main.ts -p [ tsify --noImplicitAny ] > bundle.js
```

### 使用 API

```javascript
var browserify = require("browserify");
var tsify = require("tsify");

browserify()
  .add("main.ts")
  .plugin("tsify", { noImplicitAny: true })
  .bundle()
  .pipe(process.stdout);
```

更多详情：smrq/tsify

## 第 22.2 节：Webpack

### 安装

```bash
npm install ts-loader --save-dev
```

### 基本的 webpack.config.js（webpack 2.x, 3.x）

```javascript
module.exports = {
  resolve: { extensions: ['.ts', '.tsx', '.js'] },
  module: {
    rules: [
      {
        // 为 .ts/.tsx 文件设置 ts-loader，并排除来自 node_modules 的任何导入。
        test: /\.tsx?$/,
        loaders: ['ts-loader'],
        exclude: /node_modules/
      }
    ]
  },
  entry: [
    // 将 index.tsx 设置为应用程序入口点。
    './index.tsx'
  ],
  output: { filename: "bundle.js" }
};
```

### webpack 1.x

```javascript
module.exports = {
  entry: "./src/index.tsx",
  output: { filename: "bundle.js" },
  resolve: {
    // 添加 '.ts' 和 '.tsx' 作为可解析的扩展名。
    extensions: ["", ".webpack.js", ".web.js", ".ts", ".tsx", ".js"]
  },
  module: {
    loaders: [
      // 所有带有 '.ts' 或 '.tsx' 扩展名的文件将由 'ts-loader' 处理
      { test: /\.ts(x)?$/, loader: "ts-loader", exclude: /node_modules/ }
    ]
  }
}
```

在此处查看有关 ts-loader 的更多详情。

替代方案：awesome-typescript-loader

## 第 22.3 节：Grunt

### 安装

```bash
npm install grunt-ts
```

### 基本的 Gruntfile.js

```javascript
module.exports = function (grunt) {
  grunt.initConfig({
    ts: {
      default: { src: ["**/*.ts", "!node_modules/**/*.ts"] }
    }
  });
  grunt.loadNpmTasks("grunt-ts");
  grunt.registerTask("default", ["ts"]);
};
```

更多详情：TypeStrong/grunt-ts

## 第 22.4 节：Gulp

### 安装

```bash
npm install gulp-typescript
```

### 基本的 gulpfile.js

```javascript
var gulp = require("gulp");
var ts = require("gulp-typescript");

gulp.task("default", function () {
  var tsResult = gulp.src("src/*.ts")
    .pipe(ts({ noImplicitAny: true, out: "output.js" }));
  return tsResult.js.pipe(gulp.dest("built/local"));
});
```

### 使用现有 tsconfig.json 的 gulpfile.js

```javascript
var gulp = require("gulp");
var ts = require("gulp-typescript");
var tsProject = ts.createProject('tsconfig.json', {
  noImplicitAny: true   // 你可以在此处添加和覆盖参数
});

gulp.task("default", function () {
  var tsResult = tsProject.src()
    .pipe(tsProject());
  return tsResult.js.pipe(gulp.dest('release'));
});
```

更多详情：ivogabe/gulp-typescript

## 第 22.5 节：MSBuild

更新项目文件以包含本地安装的 `Microsoft.TypeScript.Default.props`（在顶部）和 `Microsoft.TypeScript.targets`（在底部）文件：

```xml
<?xml version="1.0" encoding="utf-8" ?>
<Project ToolsVersion="4.0" DefaultTargets="Build"
  xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <!-- 在底部包含默认的 props -->
  <Import
    Project="$(MSBuildExtensionsPath32)\Microsoft\VisualStudio\v$(VisualStudioVersion)\TypeScript\Microsoft.TypeScript.Default.props"
    Condition="Exists('$(MSBuildExtensionsPath32)\Microsoft\VisualStudio\v$(VisualStudioVersion)\TypeScript\Microsoft.TypeScript.Default.props')" />

  <!-- TypeScript 配置在此处 -->
  <PropertyGroup Condition="'$(Configuration)' == 'Debug'">
    <TypeScriptRemoveComments>false</TypeScriptRemoveComments>
    <TypeScriptSourceMap>true</TypeScriptSourceMap>
  </PropertyGroup>
  <PropertyGroup Condition="'$(Configuration)' == 'Release'">
    <TypeScriptRemoveComments>true</TypeScriptRemoveComments>
    <TypeScriptSourceMap>false</TypeScriptSourceMap>
  </PropertyGroup>

  <!-- 在底部包含默认的 targets -->
  <Import
    Project="$(MSBuildExtensionsPath32)\Microsoft\VisualStudio\v$(VisualStudioVersion)\TypeScript\Microsoft.TypeScript.targets"
    Condition="Exists('$(MSBuildExtensionsPath32)\Microsoft\VisualStudio\v$(VisualStudioVersion)\TypeScript\Microsoft.TypeScript.targets')" />
</Project>
```

关于定义 MSBuild 编译器选项的更多详情：在 MSBuild 项目中设置编译器选项

## 第 22.6 节：NuGet

- 右键点击 → 管理 NuGet 包
- 搜索 `Microsoft.TypeScript.MSBuild`
- 点击 `安装`
- 安装完成后，重新构建！

更多详情可参见：包管理器对话框和使用 NuGet 的每日构建

## 第 22.7 节：安装和配置 webpack + loader

### 安装

```bash
npm install -D webpack typescript ts-loader
```

### webpack.config.js

```javascript
module.exports = {
  entry: { app: ['./src/'] },
  output: {
    path: __dirname,
    filename: './dist/[name].js',
  },
  resolve: {
    extensions: ['', '.js', '.ts'],
  },
  module: {
    loaders: [{
      test: /\.ts(x)$/,
      loaders: ['ts-loader'],
      exclude: /node_modules/
    }],
  }
};
```
