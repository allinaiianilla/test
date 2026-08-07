# 第 21 章：配置 TypeScript 项目以编译所有 TypeScript 文件

创建你的第一个 `.tsconfig` 配置文件，它将告诉 TypeScript 编译器如何处理你的 `.ts` 文件。

## 第 21.1 节：TypeScript 配置文件设置

输入命令 `"tsc --init"` 并回车。

在此之前，我们需要使用命令 `"tsc app.ts"` 来编译 ts 文件，现在这一切都在下面的配置文件中自动定义好了。

现在，你可以通过命令 `"tsc"` 来编译所有 TypeScript 文件。它会自动为你的 TypeScript 文件创建 `.js` 文件。

如果你创建另一个 TypeScript 文件并在命令提示符或终端中输入 `"tsc"` 命令，JavaScript 文件将会自动为 TypeScript 文件创建出来。
