## 第 10 章：泛型

### 10.1 泛型接口

**声明一个泛型接口**

```typescript
interface IResult<T> {
  wasSuccessful: boolean;
  error: T;
}

var result: IResult<string> = ....
var error: string = result.error;
```

**具有多个类型参数的泛型接口**

```typescript
interface IRunnable<T, U> {
  run(input: T): U;
}

var runnable: IRunnable<string, number> = ...
var input: string;
var result: number = runnable.run(input);
```

**实现一个泛型接口**

```typescript
interface IResult<T>{
  wasSuccessful: boolean;
  error: T;

  clone(): IResult<T>;
}
```

**使用泛型类实现：**

```typescript
class Result<T> implements IResult<T> {
  constructor(public result: boolean, public error: T) { }

  public clone(): IResult<T> {
    return new Result<T>(this.result, this.error);
  }
}
```

**使用非泛型类实现：**

```typescript
class StringResult implements IResult<string> {
  constructor(public result: boolean, public error: string) { }

  public clone(): IResult<string> {
    return new StringResult(this.result, this.error);
  }
}
```

### 10.2 泛型类

```typescript
class Result<T> {
  constructor(public wasSuccessful: boolean, public error: T) { }

  public clone(): Result<T> { ... }
}

let r1 = new Result(false, 'error: 42');    // Compiler infers T to string
let r2 = new Result(false, 42);             // Compiler infers T to number
let r3 = new Result<string>(true, null);    // Explicitly set T to string
let r4 = new Result<string>(true, 4);       // Compilation error because 4 is not a string
```

### 10.3 类型参数作为约束

从 TypeScript 1.8 开始，类型参数约束可以引用来自同一类型参数列表的类型参数。这在之前是错误的。

```typescript
function assign<T extends U, U>(target: T, source: U): T {
  for (let id in source) {
    target[id] = source[id];
  }
  return target;
}

let x = { a: 1, b: 2, c: 3, d: 4 };
assign(x, { b: 10, d: 20 });
assign(x, { e: 0 }); // Error
```

### 10.4 泛型约束

**简单约束：**

```typescript
interface IRunnable {
  run(): void;
}

interface IRunner<T extends IRunnable> {
  runSafe(runnable: T): void;
}
```

**更复杂的约束：**

```typescript
interface IRunnble<U> {
  run(): U;
}

interface IRunner<T extends IRunnable<U>, U> {
  runSafe(runnable: T): U;
}
```

**更复杂的约束：**

```typescript
interface IRunnble<V> {
  run(parameter: U): V;
}

interface IRunner<T extends IRunnable<U, V>, U, V> {
  runSafe(runnable: T, parameter: U): V;
}
```

**内联类型约束：**

```typescript
interface IRunnable<T extends { run(): void }> {
  runSafe(runnable: T): void;
}
```

### 10.5 泛型函数

**在接口中：**

```typescript
interface IRunner {
  runSafe<T extends IRunnable>(runnable: T): void;
}
```

**在类中：**

```typescript
class Runner implements IRunner {
  public runSafe<T extends IRunnable>(runnable: T): void {
    try {
      runnable.run();
    } catch(e) { }
  }
}
```

**简单函数：**

```typescript
function runSafe<T extends IRunnable>(runnable: T): void {
  try {
    runnable.run();
  } catch(e) { }
}
```

### 10.6 使用泛型类和泛型函数

**创建泛型类实例：**

```typescript
var stringRunnable = new Runnable<string>();
```

**运行泛型函数：**

```typescript
function runSafe<T extends Runnable<U>, U>(runnable: T);

// Specify the generic types:
runSafe<Runnable<string>, string>(stringRunnable);

// Let typescript figure the generic types by himself:
runSafe(stringRunnable);
```

---

GoalKicker.com – TypeScript Notes for Professionals 40
