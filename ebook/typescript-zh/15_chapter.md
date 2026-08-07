第 15 章：模块——导出与导入

第 15.1 节：Hello world 模块

```typescript
//hello.ts
export function hello(name: string){
    console.log(`Hello ${name}!`);
}
function helloES(name: string){
    console.log(`Hola ${name}!`);
}
export {helloES};
export default hello;
```

使用目录索引加载

如果目录中包含名为 `index.ts` 的文件，则可以仅使用目录名加载（对于 `index.ts`，文件名是可选的）。

```typescript
//welcome/index.ts
export function welcome(name: string){
    console.log(`Welcome ${name}!`);
}
```

已定义模块的使用示例

```typescript
import {hello, helloES} from "./hello";   // 加载指定元素
import defaultHello from "./hello";       // 将默认导出加载为名称 defaultHello
import * as Bundle from "./hello";        // 将所有导出加载为 Bundle
import {welcome} from "./welcome";        // 注意 index.ts 被省略了

hello("World");          // Hello World!
helloES("Mundo");        // Hola Mundo!
defaultHello("World");   // Hello World!
Bundle.hello("World");   // Hello World!
Bundle.helloES("Mundo"); // Hola Mundo!
welcome("Human");        // Welcome Human!
```

第 15.2 节：重新导出

TypeScript 支持重新导出声明。

```typescript
//Operator.ts
interface Operator {
    eval(a: number, b: number): number;
}
export default Operator;
```

```typescript
//Add.ts
import Operator from "./Operator";
export class Add implements Operator {
    eval(a: number, b: number): number {
        return a + b;
    }
}
```

```typescript
//Mul.ts
import Operator from "./Operator";
export class Mul implements Operator {
    eval(a: number, b: number): number {
        return a * b;
    }
}
```

你可以将所有操作打包到一个库中：

```typescript
//Operators.ts
import {Add} from "./Add";
import {Mul} from "./Mul";
export {Add, Mul};
```

命名声明可以使用更简洁的语法重新导出：

```typescript
//NamedOperators.ts
export {Add} from "./Add";
export {Mul} from "./Mul";
```

默认导出也可以被导出，但没有简写语法。请记住，每个模块只能有一个默认导出。

```typescript
//Calculator.ts
export {Add} from "./Add";
export {Mul} from "./Mul";
import Operator from "./Operator";
export default Operator;
```

也支持重新导出打包导入：

```typescript
//RepackedCalculator.ts
export * from "./Operators";
```

当重新导出打包时，如果显式声明，声明可以被覆盖：

```typescript
//FixedCalculator.ts
export * from "./Calculator"
import Operator from "./Calculator";
export class Add implements Operator {
    eval(a: number, b: number): number {
        return 42;
    }
}
```

使用示例：

```typescript
//run.ts
import {Add, Mul} from "./FixedCalculator";

const add = new Add();
const mul = new Mul();

console.log(add.eval(1, 1));   // 42
console.log(mul.eval(3, 4));   // 12
```

第 15.3 节：导出/导入声明

任何声明（变量、常量、函数、类等）都可以从模块中导出以供其他模块导入。TypeScript 提供两种导出类型：命名导出和默认导出。

命名导出

```typescript
// adams.ts
export function hello(name: string){
    console.log(`Hello ${name}!`);
}
export const answerToLifeTheUniverseAndEverything = 42;
export const unused = 0;
```

导入命名导出时，可以指定要导入的具体元素：

```typescript
import {hello, answerToLifeTheUniverseAndEverything} from "./adams";
hello(answerToLifeTheUniverseAndEverything);   // Hello 42!
```

默认导出

每个模块可以有一个默认导出：

```typescript
// dent.ts
const defaultValue = 54;
export default defaultValue;
```

可以通过以下方式导入：

```typescript
import dentValue from "./dent";
console.log(dentValue);   // 54
```

打包导入

TypeScript 提供了将整个模块导入为一个变量的方法：

```typescript
// adams.ts
export function hello(name: string){
    console.log(`Hello ${name}!`);
}
export const answerToLifeTheUniverseAndEverything = 42;

import * as Bundle from "./adams";
Bundle.hello(Bundle.answerToLifeTheUniverseAndEverything); // Hello 42!
console.log(Bundle.unused);  // 0
```
