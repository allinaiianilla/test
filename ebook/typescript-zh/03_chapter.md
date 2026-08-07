## 第 3 章：TypeScript 核心类型

### 3.1 字符串字面量类型

字符串字面量类型允许你指定字符串可以拥有的确切值。

```typescript
let myFavoritePet: "dog";
myFavoritePet = "dog";
```

任何其他字符串都会产生错误。

```typescript
// Error: Type '"rock"' is not assignable to type '"dog"'.
// myFavoritePet = "rock";
```

结合类型别名和联合类型，你可以获得类似枚举的行为。

```typescript
type Species = "cat" | "dog" | "bird";

function buyPet(pet: Species, name: string) : Pet { /*...*/ }

buyPet(myFavoritePet /* "dog" as defined above */ , "Rocky");

// Error: Argument of type '"rock"' is not assignable to parameter of type "'cat' | "dog" | "bird". Type '"rock"' is not assignable to type '"bird"'.
// buyPet("rock", "Rocky");
```

字符串字面量类型可用于区分重载。

```typescript
function buyPet(pet: Species, name: string) : Pet;
function buyPet(pet: "cat", name: string): Cat;
function buyPet(pet: "dog", name: string): Dog;
function buyPet(pet: "bird", name: string): Bird;
function buyPet(pet: Species, name: string) : Pet { /*...*/ }

let dog = buyPet(myFavoritePet /* "dog" as defined above */ , "Rocky");
// dog is from type Dog (dog: Dog)
```

它们非常适合用户自定义类型守卫。

```typescript
interface Pet { species: Species; eat(); sleep(); }
interface Cat extends Pet { species: "cat"; }
interface Bird extends Pet { species: "bird"; sing(); }

function petIsCat(pet: Pet): pet is Cat {
  return pet.species === "cat";
}

function petIsBird(pet: Pet): pet is Bird {
  return pet.species === "bird";
}

function playWithPet(pet: Pet){
  if (petIsCat(pet)) {
    // pet is now from type Cat (pet: Cat)
    pet.eat();
    pet.sleep();
  } else if (petIsBird(pet)) {
    // pet is now from type Bird (pet: Bird)
    pet.eat();
    pet.sing();
    pet.sleep();
  }
}
```

完整示例代码

```typescript
let myFavoritePet: "dog";
myFavoritePet = "dog";

// Error: Type '"rock"' is not assignable to type '"dog"'.
// myFavoritePet = "rock";

type Species = "cat" | "dog" | "bird";

interface Pet { species: Species; name: string; eat(); walk(); sleep(); }
interface Cat extends Pet { species: "cat"; }
interface Dog extends Pet { species: "dog"; }
interface Bird extends Pet { species: "bird"; sing(); }

// Error: Interface 'Rock' incorrectly extends interface 'Pet'. Types of property 'species' are incompatible. Type '"rock"' is not assignable to type '"cat" | "dog" | "bird"'. Type '"rock"' is not assignable to type '"bird"'.
// interface Rock extends Pet {
//   type: "rock";
// }

function buyPet(pet: Species, name: string) : Pet;
function buyPet(pet: "cat", name: string): Cat;
function buyPet(pet: "dog", name: string): Dog;
function buyPet(pet: "bird", name: string): Bird;
function buyPet(pet: Species, name: string) : Pet {
  if (pet === "cat") {
    return { species: "cat", name: name, eat: function () { console.log(`${this.name} eats.`); }, walk: function () { console.log(`${this.name} walks.`); }, sleep: function () { console.log(`${this.name} sleeps.`); } } as Cat;
  } else if (pet === "dog") {
    return { species: "dog", name: name, eat: function () { console.log(`${this.name} eats.`); }, walk: function () { console.log(`${this.name} walks.`); }, sleep: function () { console.log(`${this.name} sleeps.`); } } as Dog;
  } else if (pet === "bird") {
    return { species: "bird", name: name, eat: function () { console.log(`${this.name} eats.`); }, walk: function () { console.log(`${this.name} walks.`); }, sleep: function () { console.log(`${this.name} sleeps.`); }, sing: function () { console.log(`${this.name} sings.`); } } as Bird;
  } else {
    throw `Sorry we do not have a ${pet}. Would you like to buy a dog?`;
  }
}

function petIsCat(pet: Pet): pet is Cat {
  return pet.species === "cat";
}

function petIsDog(pet: Pet): pet is Dog {
  return pet.species === "dog";
}

function petIsBird(pet: Pet): pet is Bird {
  return pet.species === "bird";
}

function playWithPet(pet: Pet) {
  console.log(`Hey ${pet.name}, lets play.`);
  if (petIsCat(pet)) {
    // pet is now from type Cat (pet: Cat)
    pet.eat();
    pet.sleep();

    // Error: Type '"bird"' is not assignable to type '"cat"'.
    // pet.type = "bird";

    // Error: Property 'sing' does not exist on type 'Cat'.
    // pet.sing();

  } else if (petIsDog(pet)) {
    // pet is now from type Dog (pet: Dog)
    pet.eat();
    pet.walk();
    pet.sleep();
  } else if (petIsBird(pet)) {
    // pet is now from type Bird (pet: Bird)
    pet.eat();
    pet.sing();
    pet.sleep();
  } else {
    throw "An unknown pet. Did you buy a rock?";
  }
}

let dog = buyPet(myFavoritePet /* "dog" as defined above */ , "Rocky");
// dog is from type Dog (dog: Dog)

// Error: Argument of type '"rock"' is not assignable to parameter of type "'cat' | "dog" | "bird". Type '"rock"' is not assignable to type '"bird"'.
// buyPet("rock", "Rocky");

playWithPet(dog);
// Output: Hey Rocky, lets play.
//   Rocky eats.
//   Rocky walks.
//   Rocky sleeps.
```

### 3.2 元组

具有已知但可能不同类型元素的数组类型：

```typescript
let day: [number, string];
day = [0, 'Monday'];     // valid
day = ['zero', 'Monday']; // invalid: 'zero' is not numeric
console.log(day[0]); // 0
console.log(day[1]); // Monday
day[2] = 'Saturday'; // valid: [0, 'Saturday']
day[3] = false;      // invalid: must be union type of 'number | string'
```

### 3.3 Boolean

布尔值表示 TypeScript 中最基本的数据类型，用于赋 true/false 值。

```typescript
// set with initial value (either true or false)
let isTrue: boolean = true;

// defaults to 'undefined', when not explicitly set
let unsetBool: boolean;

// can also be set to 'null' as well
let nullableBool: boolean = null;
```

### 3.4 交叉类型

交叉类型将两个或多个类型的成员组合在一起。

```typescript
interface Knife { cut(); }
interface BottleOpener { openBottle(); }
interface Screwdriver { turnScrew(); }

type SwissArmyKnife = Knife & BottleOpener & Screwdriver;

function use(tool: SwissArmyKnife) {
  console.log("I can do anything!");
  tool.cut();
  tool.openBottle();
  tool.turnScrew();
}
```

### 3.5 函数参数和返回值中的类型：Number

当你在 TypeScript 中创建函数时，可以指定函数参数的数据类型和返回值的数据类型。

示例：

```typescript
function sum(x: number, y: number): number {
  return x + y;
}
```

这里的语法 `x: number, y: number` 表示该函数可以接受两个参数 x 和 y，它们只能是数字，而 `(...): number {` 表示返回值只能是数字。

用法：

```typescript
sum(84 + 76) // will be return 160
```

注意：你不能这样做

```typescript
function sum(x: string, y: string): number {
  return x + y;
}
```

或

```typescript
function sum(x: number, y: number): string {
  return x + y;
}
```

将会收到以下错误：

`error TS2322: Type 'string' is not assignable to type 'number'` 和 `error TS2322: Type 'number' is not assignable to type 'string'`

### 3.6 函数参数和返回值中的类型：String

示例：

```typescript
function hello(name: string): string {
  return `Hello ${name}!`;
}
```

这里的语法 `name: string` 表示该函数可以接受一个 `name` 参数，该参数只能是字符串，而 `(...): string {` 表示返回值只能是字符串。

用法：

```typescript
hello('StackOverflow Documentation') // will be return Hello StackOverflow Documentation!
```

### 3.7 const Enum

`const Enum` 与普通枚举相同，只是在编译时不会生成对象。相反，在使用 `const Enum` 的地方会直接替换为字面量值。

```typescript
// TypeScript: A const Enum can be defined like a normal Enum (with start value, specific values, etc.)
const enum NinjaActivity {
  Espionage,
  Sabotage,
  Assassination
}

// JavaScript: But nothing is generated

// TypeScript: Except if you use it
let myFavoriteNinjaActivity = NinjaActivity.Espionage;
console.log(myFavoritePirateActivity); // 0

// JavaScript: Then only the number of the value is compiled into the code
// var myFavoriteNinjaActivity = 0 /* Espionage */;
// console.log(myFavoritePirateActivity); // 0

// TypeScript: The same for the other constant example
console.log(NinjaActivity["Sabotage"]); // 1

// JavaScript: Just the number and in a comment the name of the value
// console.log(1 /* "Sabotage" */); // 1

// TypeScript: But without the object none runtime access is possible
// Error: A const enum member can only be accessed using a string literal.
// console.log(NinjaActivity[myFavoriteNinjaActivity]);
```

作为对比，普通枚举：

```typescript
// TypeScript: A normal Enum
enum PirateActivity {
  Boarding,
  Drinking,
  Fencing
}

// JavaScript: The Enum after the compiling
// var PirateActivity;
// (function (PirateActivity) {
//   PirateActivity[PirateActivity["Boarding"] = 0] = "Boarding";
//   PirateActivity[PirateActivity["Drinking"] = 1] = "Drinking";
//   PirateActivity[PirateActivity["Fencing"] = 2] = "Fencing";
// })(PirateActivity || (PirateActivity = {}));

// TypeScript: A normal use of this Enum
let myFavoritePirateActivity = PirateActivity.Boarding;
console.log(myFavoritePirateActivity); // 0

// JavaScript: Looks quite similar in JavaScript
// var myFavoritePirateActivity = PirateActivity.Boarding;
// console.log(myFavoritePirateActivity); // 0

// TypeScript: And some other normal use
console.log(PirateActivity["Drinking"]); // 1

// JavaScript: Looks quite similar in JavaScript
// console.log(PirateActivity["Drinking"]); // 1

// TypeScript: At runtime, you can access an normal enum
console.log(PirateActivity[myFavoritePirateActivity]); // "Boarding"

// JavaScript: And it will be resolved at runtime
// console.log(PirateActivity[myFavoritePirateActivity]); // "Boarding"
```

### 3.8 Number

与 JavaScript 一样，数字是浮点值。

```typescript
let pi: number = 3.14;           // base 10 decimal by default
let hexadecimal: number = 0xFF;  // 255 in decimal
```

ECMAScript 2015 允许二进制和八进制。

```typescript
let binary: number = 0b10;       // 2 in decimal
let octal: number = 0o755;       // 493 in decimal
```

### 3.9 String

文本数据类型：

```typescript
let singleQuotes: string = 'single';
let doubleQuotes: string = "double";
let templateString: string = `I am ${ singleQuotes }`; // I am single
```

### 3.10 Array

值的数组：

```typescript
let threePigs: number[] = [1, 2, 3];
let genericStringArray: Array<string> = ['first', '2nd', '3rd'];
```

### 3.11 Enum

一种为一组数值命名的类型：数值默认从 0 开始。

```typescript
enum Day { Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday };
let bestDay: Day = Day.Saturday;
```

设置默认起始数字：

```typescript
enum TenPlus { Ten = 10, Eleven, Twelve }
```

或手动赋值：

```typescript
enum MyOddSet { Three = 3, Five = 5, Seven = 7, Nine = 9 }
```

### 3.12 Any

当不确定类型时，可以使用 `any`：

```typescript
let anything: any = 'I am a string';
anything = 5; // but now I am the number 5
```

### 3.13 Void

如果你根本没有类型，通常用于不返回任何内容的函数：

```typescript
function log(): void {
  console.log('I return nothing');
}
```

`void` 类型只能被赋值为 `null` 或 `undefined`。

---

GoalKicker.com – TypeScript Notes for Professionals 17
