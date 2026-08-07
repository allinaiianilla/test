第 12 章：用户自定义类型守卫

第 12.1 节：类型守卫函数

你可以使用任意自定义逻辑声明作为类型守卫的函数。它们的形式如下：

```typescript
function functionName(variableName: any): variableName is DesiredType {
  // 返回 boolean 的函数体
}
```

如果函数返回 true，TypeScript 会在任何被该函数调用所守卫的代码块中将类型收窄为 `DesiredType`。例如（可尝试）：

```typescript
function isString(test: any): test is string {
  return typeof test === "string";
}

function example(foo: any) {
  if (isString(foo)) {
    // foo 在此代码块中被收窄为 string 类型
    console.log("it's a string: " + foo);
  } else {
    // foo 在此代码块中为 any 类型
    console.log("don't know what this is! [" + foo + "]");
  }
}
example("hello world");   // 打印 "it's a string: hello world"
example({ something: "else" }); // 打印 "don't know what this is! [[object Object]]"
```

守卫函数的类型谓词（函数返回类型位置的 `foo is Bar`）在编译时用于收窄类型，函数体在运行时使用。类型谓词和函数必须保持一致，否则代码将无法正常工作。

类型守卫函数不必使用 `typeof` 或 `instanceof`，它们可以使用更复杂的逻辑。例如，以下代码通过检查 jQuery 对象的版本字符串来判断你是否拥有一个 jQuery 对象。

```typescript
function isJQuery(foo): foo is JQuery {
  // 检查 jQuery 的版本字符串
  return foo.jquery !== undefined;
}

function example(foo) {
  if (isJQuery(foo)) {
    // foo 在此处被收窄为 JQuery 类型
    foo.eq(0);
  }
}
```

第 12.2 节：使用 instanceof

`instanceof` 要求变量类型为 `any`。以下代码（可尝试）：

```typescript
class Pet { }
class Dog extends Pet {
  bark() {
    console.log("woof");
  }
}
class Cat extends Pet {
  purr() {
    console.log("meow");
  }
}

function example(foo: any) {
  if (foo instanceof Dog) {
    // foo 在此代码块中为 Dog 类型
    foo.bark();
  }

  if (foo instanceof Cat) {
    // foo 在此代码块中为 Cat 类型
    foo.purr();
  }
}

example(new Dog());
example(new Cat());
```

将在控制台输出：

woof
meow

第 12.3 节：使用 typeof

`typeof` 用于区分 `number`、`string`、`boolean` 和 `symbol` 类型。其他字符串常量不会报错，但也不会用于收窄类型。与 `instanceof` 不同，`typeof` 可以作用于任何类型的变量。在以下示例中，`foo` 可以被声明为 `number | string` 类型而不会有问题。以下代码（可尝试）：

```typescript
function example(foo: any) {
  if (typeof foo === "number") {
    // foo 在此代码块中为 number 类型
    console.log(foo + 100);
  }

  if (typeof foo === "string") {
    // foo 在此代码块中为 string 类型
    console.log("not a number: " + foo);
  }
}
example(23);
example("foo");
```

输出：

123
not a number: foo
