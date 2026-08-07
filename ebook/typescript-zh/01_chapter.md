# 第 1 章：开始使用 TypeScript

## 版本历史

| 版本 | 发布日期 |
|------|----------|
| 2.8.3 | 2018-04-20 |
| 2.8 | 2018-03-28 |
| 2.8 RC | 2018-03-16 |
| 2.7.2 | 2018-02-16 |
| 2.7.1 | 2018-02-01 |
| 2.7 beta | 2018-01-18 |
| 2.6.1 | 2017-11-01 |
| 2.5.2 | 2017-09-01 |
| 2.4.1 | 2017-06-28 |
| 2.3.2 | 2017-04-28 |
| 2.3.1 | 2017-04-25 |
| 2.3.0 beta | 2017-04-04 |
| 2.2.2 | 2017-03-13 |
| 2.2 | 2017-02-17 |
| 2.1.6 | 2017-02-07 |
| 2.2 beta | 2017-02-02 |
| 2.1.5 | 2017-01-05 |
| 2.1.4 | 2016-12-05 |
| 2.0.8 | 2016-11-08 |
| 2.0.7 | 2016-11-03 |
| 2.0.6 | 2016-10-23 |
| 2.0.5 | 2016-09-22 |
| 2.0 Beta | 2016-07-08 |
| 1.8.10 | 2016-04-09 |
| 1.8.9 | 2016-03-16 |
| 1.8.5 | 2016-03-02 |
| 1.8.2 | 2016-02-17 |
| 1.7.5 | 2015-12-14 |
| 1.7 | 2015-11-20 |
| 1.6 | 2015-09-11 |
| 1.5.4 | 2015-07-15 |
| 1.5 | 2015-07-15 |
| 1.4 | 2015-01-13 |
| 1.3 | 2014-10-28 |
| 1.1.0.1 | 2014-09-23 |

## 1.1：安装与设置

### 背景

TypeScript 是 JavaScript 的一个类型化超集，可直接编译为 JavaScript 代码。TypeScript 文件通常使用 `.ts` 扩展名。许多 IDE 无需额外设置即可支持 TypeScript，但 TypeScript 也可以通过命令行使用 TypeScript Node.JS 包进行编译。

### IDE

- **Visual Studio**——Visual Studio 2015 内置 TypeScript。Visual Studio 2013 Update 2 或更高版本也包含 TypeScript，或者你可以为更早的版本下载 TypeScript。
- **Visual Studio Code**——Visual Studio Code（vscode）为 TypeScript 提供了上下文自动补全以及重构和调试工具。vscode 本身是用 TypeScript 实现的。支持 Mac OS X、Windows 和 Linux。
- **WebStorm**——WebStorm 2016.2 自带 TypeScript 以及内置编译器。[WebStorm 并非免费]
- **IntelliJ IDEA**——IntelliJ IDEA 2016.2 通过 JetBrains 团队维护的插件支持 TypeScript 和编译器。[IntelliJ 并非免费]
- **Atom & atom-typescript**——Atom 通过 atom-typescript 包支持 TypeScript。
- **Sublime Text**——Sublime Text 通过 TypeScript 包支持 TypeScript。

### 安装命令行界面

**安装 Node.js**

**全局安装 npm 包**

你可以全局安装 TypeScript，以便从任何目录访问它。

```bash
npm install -g typescript
```

**本地安装 npm 包**

你可以本地安装 TypeScript 并保存到 `package.json` 以限定在某个目录中使用。

```bash
npm install typescript --save-dev
```

### 安装渠道

你可以从以下渠道安装：

- 稳定版渠道：`npm install typescript`
- Beta 版渠道：`npm install typescript@beta`
- 开发版渠道：`npm install typescript@next`

### 编译 TypeScript 代码

`tsc` 编译命令随 `typescript` 一起提供，可用于编译代码。

```bash
tsc my-code.ts
```

这会创建一个 `my-code.js` 文件。

### 使用 tsconfig.json 编译

你还可以通过 `tsconfig.json` 文件提供随代码一起的编译选项。要启动一个新的 TypeScript 项目，在终端窗口中 `cd` 到项目根目录并运行 `tsc --init`。此命令将生成一个包含最小配置选项的 `tsconfig.json` 文件，类似以下内容：

```json
{
  "compilerOptions": {
    "module": "commonjs",
    "target": "es5",
    "noImplicitAny": false,
    "sourceMap": false,
    "pretty": true
  },
  "exclude": [
    "node_modules"
  ]
}
```

将 `tsconfig.json` 文件放置在 TypeScript 项目根目录后，你可以使用 `tsc` 命令运行编译。

---

## 1.2：基本语法

TypeScript 是 JavaScript 的一个类型化超集，这意味着所有 JavaScript 代码都是有效的 TypeScript 代码。TypeScript 在此基础上增加了许多新特性。TypeScript 使 JavaScript 更像一种类似于 C# 和 Java 的强类型、面向对象的语言。这意味着 TypeScript 代码往往更适合大型项目，并且代码往往更容易理解和维护。强类型也意味着该语言可以（并且确实）被预编译，并且变量不能被赋予超出其声明范围的值。例如，当一个 TypeScript 变量被声明为 number 时，你不能给它赋予文本值。这种强类型和面向对象的特性使 TypeScript 更容易调试和维护，而这正是标准 JavaScript 最薄弱的两个方面。

### 类型声明

你可以为变量、函数参数和函数返回类型添加类型声明。类型写在变量名后面的冒号之后，如下所示：

```typescript
var num: number = 5;
```

编译器将在编译期间（尽可能）检查类型并报告类型错误。

```typescript
var num: number = 5;
num = "this is a string";  // 错误：类型 'string' 不可分配给类型 'number'
```

基本类型有：

- **`number`**——包括整数和浮点数
- **`string`**
- **`boolean`**
- **`Array`**——你可以指定数组元素的类型。有两种等价的方式来定义数组类型：`Array<T>` 和 `T[]`。例如：
  - `number[]`——数字数组
  - `Array<string>`——字符串数组
- **元组（Tuple）**——元组具有固定数量的元素，每个元素有特定类型。
  - `[boolean, string]`——第一个元素是 boolean、第二个是 string 的元组
  - `[number, number, number]`——三个数字的元组
- **`{}`**——对象，你可以定义其属性或索引器
  - `{name: string, age: number}`——具有 name 和 age 属性的对象
  - `{[key: string]: number}`——以 string 为键的数字字典
- **`enum`**——`{ Red = 0, Blue, Green }`——映射到数字的枚举
- **`Function`**——你为参数和返回值指定类型：
  - `(param: number) => string`——接受一个 number 参数并返回 string 的函数
  - `() => number`——无参数返回 number 的函数
  - `(a: string, b?: boolean) => void`——接受一个 string 和一个可选的 boolean，无返回值的函数
- **`any`**——允许任何类型。涉及 `any` 的表达式不进行类型检查。
- **`void`**——表示"无"，可用作函数返回值。只有 `null` 和 `undefined` 属于 `void` 类型。
- **`never`**
  - `let foo: never;`——作为永远不为 true 的类型守卫下变量的类型
  - `function error(message: string): never { throw new Error(message); }`——作为永不返回的函数的返回类型
- **`null`**——值 `null` 的类型。`null` 隐式地属于每种类型的一部分，除非启用了严格空值检查。

### 类型转换

你可以通过尖括号执行显式类型转换，例如：

```typescript
var derived: MyInterface;
(<ImplementingClass>derived).someSpecificMethod();
```

这个例子展示了一个被编译器视为 `MyInterface` 的 `derived` 类。如果没有第二行的类型转换，编译器会抛出异常，因为它不理解 `someSpecificMethod()`，但通过 `<ImplementingClass>derived` 进行类型转换告诉编译器该怎么做。TypeScript 中另一种类型转换方式是使用 `as` 关键字：

```typescript
var derived: MyInterface;
(derived as ImplementingClass).someSpecificMethod();
```

从 TypeScript 1.6 开始，默认使用 `as` 关键字，因为在 `.jsx` 文件中使用 `<>` 会产生歧义。这一点在 TypeScript 官方文档中有说明。

### 类

类可以在 TypeScript 代码中定义和使用。要了解更多关于类的信息，请参阅"类"文档页面。

---

## 1.3：Hello World

```typescript
class Greeter {
  greeting: string;
  constructor(message: string) {
    this.greeting = message;
  }
  greet(): string {
    return this.greeting;
  }
}

let greeter = new Greeter("Hello, world!");
console.log(greeter.greet());
```

这里我们有一个类 `Greeter`，它有一个 `constructor` 和一个 `greet` 方法。我们可以使用 `new` 关键字构造该类的一个实例，并传入一个字符串，让 `greet` 方法输出到控制台。我们的 `Greeter` 类实例存储在 `greeter` 变量中，然后我们用该变量调用 `greet` 方法。

---

## 1.4：使用 ts-node 运行 TypeScript

ts-node 是一个 npm 包，允许用户直接运行 TypeScript 文件，无需通过 `tsc` 进行预编译。它还提供 REPL。

全局安装 ts-node：

```bash
npm install -g ts-node
```

ts-node 不包含 TypeScript 编译器，所以你可能需要单独安装。

```bash
npm install -g typescript
```

### 执行脚本

要执行名为 `main.ts` 的脚本，运行：

```bash
ts-node main.ts
```

```typescript
// main.ts
console.log("Hello world");
```

**使用示例**

```bash
$ ts-node main.ts
Hello world
```

### 运行 REPL

要运行 REPL，执行命令 `ts-node`。

**使用示例**

```bash
$ ts-node
> const sum = (a, b): number => a + b;
undefined
> sum(2, 2)
4
> .exit
```

要退出 REPL，使用命令 `.exit` 或按两次 `CTRL+C`。

---

## 1.5：在 Node.js 中使用 TypeScript REPL

要在 Node.js 中使用 TypeScript REPL，你可以使用 tsun 包。

全局安装：

```bash
npm install -g tsun
```

然后在终端或命令提示符中使用 `tsun` 命令运行。

**使用示例：**

```bash
$ tsun
TSUN : TypeScript Upgraded Node
type in TypeScript expression to evaluate
type :help for commands in repl
$ function multiply(x, y) {
.. return x * y;
..}
undefined
$ multiply(3, 4)
12
```
