# 第 24 章：TypeScript 与 AngularJS

| 名称 | 描述 |
|------|------|
| `controllerAs` | 别名，变量或函数可以赋值给它。@see: https://docs.angularjs.org/guide/directive |
| `$inject` | 依赖注入列表，由 Angular 解析并作为参数传递给构造函数。 |

## 第 24.1 节：指令（Directive）

```typescript
interface IMyDirectiveController {
  // 在此指定暴露的控制器方法和属性
  getUrl(): string;
}

class MyDirectiveController implements IMyDirectiveController {
  // 内部注入，每个指令独立
  public static $inject = ["$location", "toaster"];

  constructor(private $location: ng.ILocationService, private toaster: any) {
    // $location 和 toaster 现在是控制器的属性
  }

  public getUrl(): string {
    return this.$location.url(); // 利用 $location 来获取 URL
  }
}

/*
 * 外部注入，用于一次运行的控制。
 * 例如，我们将所有模板放在一个值中，并希望使用它。
 */
export function myDirective(templatesUrl: ITemplates): ng.IDirective {
  return {
    controller: MyDirectiveController,
    controllerAs: "vm",
    link: (scope: ng.IScope,
           element: ng.IAugmentedJQuery,
           attributes: ng.IAttributes,
           controller: IMyDirectiveController): void => {
      let url = controller.getUrl();
      element.text("Current URL: " + url);
    },
    replace: true,
    require: "ngModel",
    restrict: "A",
    templateUrl: templatesUrl.myDirective,
  };
}

myDirective.$inject = [Templates.prototype.slug];

// 在项目中统一使用 slug 命名可以简化指令名称的更改
myDirective.prototype.slug = "myDirective";

// 你可以将其放在某个引导文件中，或者放在同一个文件中
angular.module("myApp")
  .directive(myDirective.prototype.slug, myDirective);
```

## 第 24.2 节：简单示例

```typescript
export function myDirective($location: ng.ILocationService): ng.IDirective {
  return {
    link: (scope: ng.IScope,
           element: ng.IAugmentedJQuery,
           attributes: ng.IAttributes): void => {
      element.text("Current URL: " + $location.url());
    },
    replace: true,
    require: "ngModel",
    restrict: "A",
    templateUrl: templatesUrl.myDirective,
  };
}

// 在项目中统一使用 slug 命名可以简化指令名称的更改
myDirective.prototype.slug = "myDirective";

// 你可以将其放在某个引导文件中，或者放在同一个文件中
angular.module("myApp")
  .directive(myDirective.prototype.slug,
    [Templates.prototype.slug, myDirective]);
```

## 第 24.3 节：组件（Component）

为了更容易地过渡到 Angular 2，建议使用 `Component`（从 Angular 1.5.8 开始可用）。

### myModule.ts

```typescript
import { MyModuleComponent } from "./components/myModuleComponent";
import { MyModuleService } from "./services/MyModuleService";

angular
  .module("myModule", [])
  .component("myModuleComponent", new MyModuleComponent())
  .service("myModuleService", MyModuleService);
```

### components/myModuleComponent.ts

```typescript
import IComponentOptions = angular.IComponentOptions;
import IControllerConstructor = angular.IControllerConstructor;
import Injectable = angular.Injectable;
import { MyModuleController } from "../controller/MyModuleController";

export class MyModuleComponent implements IComponentOptions {
  public templateUrl: string = "./app/myModule/templates/myComponentTemplate.html";
  public controller: Injectable<IControllerConstructor> = MyModuleController;
  public bindings: {[boundProperty: string]: string} = {};
}
```

### templates/myModuleComponent.html

```html
<div class="my-module-component">
  {{$ctrl.someContent}}
</div>
```

### controller/MyModuleController.ts

```typescript
import IController = angular.IController;
import { MyModuleService } from "../services/MyModuleService";

export class MyModuleController implements IController {
  public static readonly $inject: string[] = ["$element", "myModuleService"];
  public someContent: string = "Hello World";

  constructor($element: JQuery, private myModuleService: MyModuleService) {
    console.log("element", $element);
  }

  public doSomething(): void {
    // 实现...
  }
}
```

### services/MyModuleService.ts

```typescript
export class MyModuleService {
  public static readonly $inject: string[] = [];

  constructor() { }

  public doSomething(): void {
    // 执行某些操作
  }
}
```

### somewhere.html

```html
<my-module-component></my-module-component>
```
