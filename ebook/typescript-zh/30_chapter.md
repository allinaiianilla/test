# 第 30 章：单元测试

## 第 30.1 节：tape

tape 是一个极简的 JavaScript 测试框架，它输出 TAP 兼容格式的标记。

要使用 `npm` 安装 `tape`，运行命令：

```bash
npm install --save-dev tape @types/tape
```

要在 TypeScript 中使用 `tape`，你需要将 `ts-node` 安装为全局包，运行以下命令：

```bash
npm install -g ts-node
```

现在你可以开始编写你的第一个测试了：

```typescript
//math.test.ts
import * as test from "tape";

test("Math test", (t) => {
  t.equal(4, 2 + 2);
  t.true(5 > 2 + 2);
  t.end();
});
```

要执行测试，运行命令：

```bash
ts-node node_modules/tape/bin/tape math.test.ts
```

在输出中你应该看到：

```
TAP version 13
# Math test
ok 1 should be equal
ok 2 should be truthy

1..2
# tests 2
# pass 2

# ok
```

干得好，你刚刚运行了你的 TypeScript 测试。

### 运行多个测试文件

你可以使用路径通配符一次运行多个测试文件。要执行 `tests` 目录中的所有 TypeScript 测试，运行命令：

```bash
ts-node node_modules/tape/bin/tape tests/**/*.ts
```

## 第 30.2 节：jest（ts-jest）

jest 是 Facebook 出品的无痛 JavaScript 测试框架，通过 ts-jest 可以用于测试 TypeScript 代码。

要使用 npm 安装 jest，运行命令：

```bash
npm install --save-dev jest @types/jest ts-jest typescript
```

为了便于使用，将 `jest` 安装为全局包：

```bash
npm install -g jest
```

要使 `jest` 与 TypeScript 配合使用，你需要在 `package.json` 中添加配置：

```json
//package.json
{
  ...
  "jest": {
    "transform": {
      ".(ts|tsx)": "<rootDir>/node_modules/ts-jest/preprocessor.js"
    },
    "testRegex": "(/__tests__/.*|\\.(test|spec))\\.(ts|tsx|js)$",
    "moduleFileExtensions": ["ts", "tsx", "js"]
  }
}
```

现在 `jest` 已经准备好了。假设我们有一个示例 fizz buzz 需要测试：

```typescript
//fizzBuzz.ts
export function fizzBuzz(n: number): string {
  let output = "";
  for (let i = 1; i <= n; i++) {
    if (i % 5 && i % 3) {
      output += i + ' ';
    }
    if (i % 3 === 0) {
      output += 'Fizz ';
    }
    if (i % 5 === 0) {
      output += 'Buzz ';
    }
  }
  return output;
}
```

示例测试可能如下所示：

```typescript
//FizzBuzz.test.ts
/// <reference types="jest" />

import {fizzBuzz} from "./fizzBuzz";

test("FizzBuzz test", () => {
  expect(fizzBuzz(2)).toBe("1 2 ");
  expect(fizzBuzz(3)).toBe("1 2 Fizz ");
});
```

要执行测试，运行：

```bash
jest
```

在输出中你应该看到：

```
PASS  ./fizzBuzz.test.ts
  ✓ FizzBuzz test (3ms)

Test Suites: 1 passed, 1 total
Tests:       1 passed, 1 total
Snapshots:   0 total
Time:        1.46s, estimated 2s
Ran all test suites.
```

### 代码覆盖率

`jest` 支持生成代码覆盖率报告。要在 TypeScript 中使用代码覆盖率，你需要在 `package.json` 中添加另一行配置。

```json
{
  ...
  "jest": {
    ...
    "testResultsProcessor": "<rootDir>/node_modules/ts-jest/coverageprocessor.js"
  }
}
```

要运行测试并生成覆盖率报告，运行：

```bash
jest --coverage
```

如果与我们的示例 fizz buzz 一起使用，你应该看到：

```
PASS  ./fizzBuzz.test.ts
  ✓ FizzBuzz test (3ms)

-------------|----------|----------|----------|----------|----------------|
File         | % Stmts  | % Branch | % Funcs  | % Lines  |Uncovered Lines |
-------------|----------|----------|----------|----------|----------------|
All files    |   92.31  |   87.5   |   100    |   91.67  |                |
 fizzBuzz.ts |   92.31  |   87.5   |   100    |   91.67  |       13       |
-------------|----------|----------|----------|----------|----------------|

Test Suites: 1 passed, 1 total
Tests:       1 passed, 1 total
Snapshots:   0 total
Time:        1.857s
Ran all test suites.
```

`jest` 还创建了 `coverage` 文件夹，其中包含各种格式的覆盖率报告，包括位于 `coverage/lcov-report/index.html` 中的用户友好 HTML 报告。

## 第 30.3 节：Alsatian

Alsatian 是一个用 TypeScript 编写的单元测试框架。它允许使用测试用例，并输出 TAP 兼容格式的标记。

要使用它，请从 `npm` 安装：

```bash
npm install alsatian --save-dev
```

然后设置一个测试文件：

```typescript
import { Expect, Test, TestCase } from "alsatian";
import { SomeModule } from "../src/some-module";

export SomeModuleTests {

  @Test()
  public statusShouldBeTrueByDefault() {
    let instance = new SomeModule();
    Expect(instance.status).toBe(true);
  }

  @Test("Name should be null by default")
  public nameShouldBeNullByDefault() {
    let instance = new SomeModule();
    Expect(instance.name).toBe(null);
  }

  @TestCase("first name")
  @TestCase("apples")
  public shouldSetNameCorrectly(name: string) {
    let instance = new SomeModule();
    instance.setName(name);
    Expect(instance.name).toBe(name);
  }
}
```

有关完整文档，请参阅 Alsatian 的 GitHub 仓库。

## 第 30.4 节：chai-immutable 插件

**1. 从 npm 安装 chai、chai-immutable 和 ts-node**

```bash
npm install --save-dev chai chai-immutable ts-node
```

**2. 安装 mocha 和 chai 的类型定义**

```bash
npm install --save-dev @types/mocha @types/chai
```

**3. 编写简单的测试文件：**

```typescript
import {List, Set} from 'immutable';
import * as chai from 'chai';
import * as chaiImmutable from 'chai-immutable';

chai.use(chaiImmutable);

describe('chai immutable example', () => {
  it('example', () => {
    expect(Set.of(1,2,3)).to.not.be.empty;
    expect(Set.of(1,2,3)).to.include(2);
    expect(Set.of(1,2,3)).to.include(5);
  })
})
```

**4. 在控制台中运行：**

```bash
mocha --compilers ts:ts-node/register,tsx:ts-node/register 'test/**/*.spec.@(ts|tsx)'
```
