# 第 29 章：调试

运行和调试 TypeScript 有两种方式：

1. **转译为 JavaScript**，在 node 中运行，并使用映射链接回 TypeScript 源文件，或者
2. **直接运行 TypeScript**，使用 ts-node

本文介绍了使用 Visual Studio Code 和 WebStorm 的两种方式。所有示例均假设你的主文件是 `index.ts`。

## 第 29.1 节：在 WebStorm 中使用 ts-node 调试 TypeScript

将以下脚本添加到你的 `package.json` 中：

```json
"start:idea": "ts-node %NODE_DEBUG_OPTION% --ignore false index.ts"
```

右键点击该脚本，选择 `创建 'test:idea'...` 并点击 `确定` 以创建调试配置：

使用此配置启动调试器：

## 第 29.2 节：在 Visual Studio Code 中使用 ts-node 调试 TypeScript

将 ts-node 添加到你的 TypeScript 项目中：

```bash
npm i ts-node
```

将脚本添加到你的 `package.json` 中：

```json
"start:debug": "ts-node --inspect=5858 --debug-brk --ignore false index.ts"
```

`launch.json` 需要配置为使用 `node2` 类型，并启动 npm 运行 `start:debug` 脚本：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node2",
      "request": "launch",
      "name": "Launch Program",
      "runtimeExecutable": "npm",
      "windows": {
        "runtimeExecutable": "npm.cmd"
      },
      "runtimeArgs": [
        "run-script",
        "start:debug"
      ],
      "cwd": "${workspaceRoot}/server",
      "outFiles": [],
      "port": 5858,
      "sourceMaps": true
    }
  ]
}
```

## 第 29.3 节：在 Visual Studio Code 中使用 SourceMaps 调试 JavaScript

在 `tsconfig.json` 中设置：

```json
"sourceMap": true,
```

以便在使用 `tsc` 命令时，从 TypeScript 源文件生成映射以及 js 文件。

`launch.json` 文件：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Launch Program",
      "program": "${workspaceRoot}\\index.js",
      "cwd": "${workspaceRoot}",
      "outFiles": [],
      "sourceMaps": true
    }
  ]
}
```

这将使用生成的 index.js（如果你的主文件是 index.ts）启动 node，并在 Visual Studio Code 中启动调试器，该调试器会在断点处停止并解析 TypeScript 代码中的变量值。

## 第 29.4 节：在 WebStorm 中使用 SourceMaps 调试 JavaScript

创建一个 `Node.js` 调试配置，并使用 `index.js` 作为 `Node 参数`。
