# 第 27 章：TSLint - 确保代码质量和一致性

TSLint 对代码进行静态分析，并检测代码中的错误和潜在问题。

## 第 27.1 节：减少编程错误的配置

此 `tslint.json` 示例包含一组配置，用于强制执行更多类型检查、捕获常见错误或容易产生 bug 的易混淆结构，并更严格地遵循 TypeScript 贡献者编码指南。要强制执行这些规则，请将 tslint 包含在你的构建流程中，并在使用 tsc 编译之前检查你的代码。

```json
{
  "rules": {
    // TypeScript 特定
    "member-access": true,    // 要求对类成员进行显式的可见性声明。
    "no-any": true,           // 禁止使用 any 作为类型声明。

    // 功能性
    "label-position": true,        // 仅允许标签在合理的位置。
    "no-bitwise": true,            // 禁止使用位运算符。
    "no-eval": true,               // 禁止使用 eval 函数调用。
    "no-null-keyword": true,       // 禁止使用 null 关键字字面量。
    "no-unsafe-finally": true,     // 禁止在 finally 块中使用控制流语句，如 return、continue、break 和 throws。
    "no-var-keyword": true,        // 禁止使用 var 关键字。
    "radix": true,                 // 要求在调用 parseInt 时指定基数参数。
    "triple-equals": true,         // 要求使用 === 和 !== 代替 == 和 !=。
    "use-isnan": true,             // 强制使用 isNaN() 函数检查 NaN 引用，而不是与 NaN 常量比较。

    // 风格
    "class-name": true,                     // 强制使用 PascalCase 命名的类和接口名称。
    "interface-name": [true, "never-prefix"], // 要求接口名称以大写字母 'I' 开头
    "no-angle-bracket-type-assertion": true,  // 要求使用 as Type 进行类型断言，而不是 <Type>。
    "one-variable-per-declaration": true,     // 禁止在同一声明语句中定义多个变量。
    "quotemark": [true, "double", "avoid-escape"], // 要求字符串字面量使用双引号。
    "semicolon": [true, "always"],            // 强制在每条语句末尾使用一致的分号。
    "variable-name": [true, "ban-keywords", "check-format", "allow-leading-underscore"]
      // 检查变量名称的各种错误。禁止使用某些 TypeScript 关键字
      // （any, Number, number, String, string, Boolean, boolean, undefined）作为变量或参数。
      // 仅允许 camelCase 或 UPPER_CASED 变量名。允许开头使用下划线
      // （仅在指定 "check-format" 时生效）。
  }
}
```

## 第 27.2 节：安装和设置

要安装 tslint，运行命令：

```bash
npm install -g tslint
```

Tslint 通过 `tslint.json` 文件进行配置。要初始化默认配置，运行命令：

```bash
tslint --init
```

要检查文件中可能存在的错误，运行命令：

```bash
tslint filename.ts
```

## 第 27.3 节：TSLint 规则集

- tslint-microsoft-contrib
- tslint-eslint-rules
- codelyzer

Yeoman 生成器支持所有这些预设，并且也可以扩展：generator-tslint

## 第 27.4 节：基本的 tslint.json 设置

这是一个基本的 `tslint.json` 设置，它：

- 阻止使用 `any`
- 要求 `if/else/for/do/while` 语句使用花括号
- 要求字符串使用双引号（`"`）

```json
{
  "rules": {
    "no-any": true,
    "curly": true,
    "quotemark": [true, "double"]
  }
}
```

## 第 27.5 节：使用预定义规则集作为默认值

`tslint` 可以扩展现有的规则集，并随附了默认的 `tslint:recommended` 和 `tslint:latest`。

- **`tslint:recommended`** 是一组稳定、有一定倾向性的规则，我们推荐用于一般的 TypeScript 编程。此配置遵循 semver，因此在次版本或补丁版本中不会有破坏性更改。
- **`tslint:latest`** 扩展了 `tslint:recommended`，并会持续更新以包含每个 TSLint 版本中最新的规则配置。使用此配置可能会在次版本中引入破坏性更改，因为新启用的规则可能会导致你的代码出现 lint 失败。当 TSLint 达到大版本升级时，`tslint:recommended` 将更新为与 `tslint:latest` 相同。

预定义规则集的文档和源代码。

因此，你可以简单地使用：

```json
{
  "extends": "tslint:recommended"
}
```

来获得一个合理的起始配置。然后可以通过 `rules` 覆盖该预设中的规则，例如，对于 node 开发者来说，将 `no-console` 设置为 `false` 是有意义的：

```json
{
  "extends": "tslint:recommended",
  "rules": {
    "no-console": false
  }
}
```
