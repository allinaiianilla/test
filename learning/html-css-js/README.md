<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HTML · CSS · JS 速查手册 —— 写码时开着的那一页</title>
<style>
  :root {
    --bg: #fffdf9; --fg: #1c1917; --muted: #78716c; --line: #e7e5e4;
    --orange: #ea580c; --orange-soft: #fff7ed;
    --code-bg: #292524; --code-fg: #fafaf9;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--fg); line-height: 1.65; font-size: 14.5px;
  }
  .wrap { max-width: 900px; margin: 0 auto; padding: 36px 18px 90px; }
  header { margin-bottom: 30px; }
  .kicker { color: var(--orange); font-size: 12.5px; letter-spacing: 2px; font-weight: 700; }
  h1 { font-size: 28px; font-weight: 800; letter-spacing: -.4px; margin-top: 4px; }
  header p { color: var(--muted); margin-top: 6px; font-size: 14px; }

  /* 粘性目录条 */
  .quicknav {
    position: sticky; top: 0; z-index: 10;
    background: rgba(255,253,249,.95); backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--line);
    display: flex; gap: 4px; padding: 10px 2px; margin-bottom: 34px;
    overflow-x: auto;
  }
  .quicknav a {
    flex-shrink: 0; padding: 5px 14px; border-radius: 999px; text-decoration: none;
    color: var(--muted); font-size: 13px; font-weight: 600; border: 1px solid transparent;
  }
  .quicknav a:hover { color: var(--orange); background: var(--orange-soft); }

  section { margin-bottom: 54px; }
  h2 { font-size: 20px; font-weight: 800; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; }
  h2 .ico { font-size: 22px; }
  h2 small { font-size: 12.5px; color: var(--muted); font-weight: 400; }
  h3 { font-size: 15px; color: var(--muted); margin: 18px 0 8px; font-weight: 600; }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  @media (max-width: 640px) { .grid { grid-template-columns: 1fr; } }

  .card { background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
  .card b.t { display: block; font-size: 13.5px; margin-bottom: 6px; }
  pre {
    background: var(--code-bg); color: var(--code-fg);
    padding: 12px 14px; border-radius: 10px; overflow-x: auto;
    font-family: ui-monospace, "SF Mono", Consolas, monospace;
    font-size: 12.5px; line-height: 1.7; tab-size: 2;
  }
  pre .c { color: #a8a29e; }        /* 注释 */
  pre .k { color: #fdba74; }        /* 关键/标签名 */
  pre .s { color: #86efac; }        /* 字符串 */
  table { border-collapse: collapse; width: 100%; font-size: 13px; background: #fff; }
  th, td { border: 1px solid var(--line); padding: 6px 10px; text-align: left; vertical-align: top; }
  th { background: var(--orange-soft); font-weight: 700; white-space: nowrap; }
  td code { font-family: ui-monospace, monospace; font-size: 12.5px; background: #f5f5f4; padding: 1px 5px; border-radius: 4px; }
  td b { font-weight: 700; }

  .copy-hint { color: var(--muted); font-size: 12px; margin-top: 8px; }
  footer { color: var(--muted); font-size: 12.5px; text-align: center; margin-top: 60px; }
</style>
</head>
<body>
<div class="wrap">

<header>
  <div class="kicker">速查手册 · 第三套</div>
  <h1>HTML · CSS · JS 速查手册</h1>
  <p>写码时开着的那一页。只放高频、能直接抄的内容。忘了什么 → 顶部导航跳过去 → 复制走人。</p>
</header>

<nav class="quicknav">
  <a href="#html">🏗 HTML</a>
  <a href="#css-box">📦 CSS 盒模型</a>
  <a href="#css-flex">📐 CSS Flex</a>
  <a href="#css-common">🎨 CSS 常用</a>
  <a href="#js-syntax">⚡ JS 语法</a>
  <a href="#js-dom">🖱 JS DOM</a>
  <a href="#js-array">📚 JS 数组</a>
  <a href="#gotchas">🕳 常见坑</a>
</nav>

<!-- ============ HTML ============ -->
<section id="html">
  <h2><span class="ico">🏗</span>HTML 骨架与常用标签 <small>结构层</small></h2>
  <div class="grid">
    <div class="card">
      <b class="t">页面模板（每次新建从这里抄）</b>
<pre>&lt;!DOCTYPE html&gt;
&lt;html lang="zh-CN"&gt;
&lt;head&gt;
  &lt;meta charset="UTF-8"&gt;
  &lt;meta name="viewport"
        content="width=device-width, initial-scale=1.0"&gt;
  &lt;title&gt;页面标题&lt;/title&gt;
  &lt;link rel="stylesheet" href="style.css"&gt;
&lt;/head&gt;
&lt;body&gt;
  &lt;script src="app.js"&gt;&lt;/script&gt;
&lt;/body&gt;
&lt;/html&gt;</pre>
      <div class="copy-hint">viewport 那行管手机适配，别删</div>
    </div>
    <div class="card">
      <b class="t">高频标签</b>
<pre>&lt;h1&gt;标题&lt;/h1&gt;          &lt;p&gt;段落&lt;/p&gt;
&lt;a href="url"&gt;链接&lt;/a&gt;  &lt;img src="x.png" alt="描述"&gt;
&lt;button&gt;按钮&lt;/button&gt;   &lt;ul&gt;&lt;li&gt;列表&lt;/li&gt;&lt;/ul&gt;
&lt;div&gt;块容器&lt;/div&gt;      &lt;span&gt;行内容器&lt;/span&gt;

&lt;input type="text" placeholder="提示"&gt;
&lt;input type="checkbox"&gt;  &lt;input type="radio"&gt;
&lt;select&gt;&lt;option&gt;下拉&lt;/option&gt;&lt;/select&gt;
&lt;textarea&gt;长文本&lt;/textarea&gt;</pre>
    </div>
  </div>
  <h3>语义化标签（比 div 更有意义的容器）</h3>
  <table>
    <tr><th>标签</th><th>用途</th><th>标签</th><th>用途</th></tr>
    <tr><td><code>&lt;header&gt;</code></td><td>页头</td><td><code>&lt;footer&gt;</code></td><td>页脚</td></tr>
    <tr><td><code>&lt;nav&gt;</code></td><td>导航</td><td><code>&lt;main&gt;</code></td><td>主体（每页仅一个）</td></tr>
    <tr><td><code>&lt;section&gt;</code></td><td>章节</td><td><code>&lt;article&gt;</code></td><td>独立内容块</td></tr>
    <tr><td><code>&lt;form&gt;</code></td><td>表单区</td><td><code>&lt;table&gt;</code></td><td>表格</td></tr>
  </table>
</section>

<!-- ============ CSS 盒模型 ============ -->
<section id="css-box">
  <h2><span class="ico">📦</span>CSS 盒模型 <small>一切布局的底层</small></h2>
  <div class="grid">
    <div class="card">
      <b class="t">从里到外四层</b>
<pre>content 内容 → padding 内距
→ border 边框 → margin 外距

.box {
  width: 200px;
  padding: 16px;        /* 四周同值 */
  padding: 8px 16px;    /* 上下 左右 */
  margin: 24px auto;    /* auto = 水平居中 */
  border: 2px solid #333;
  border-radius: 12px;  /* 圆角 */
}</pre>
    </div>
    <div class="card">
      <b class="t">必背：让宽度计算符合直觉</b>
<pre>/* 默认 width 只算内容，
   加 padding 会撑大盒子。
   加上这句后 width = 最终宽度： */
*, *::before, *::after {
  box-sizing: border-box;
}

/* 居中三板斧 */
margin: 0 auto;               /* 块级水平居中 */
display: flex; justify-content: center;  /* flex */
position: absolute; top: 50%; left: 50%;
transform: translate(-50%, -50%);        /* 绝对居中 */</pre>
    </div>
  </div>
</section>

<!-- ============ CSS Flex ============ -->
<section id="css-flex">
  <h2><span class="ico">📐</span>CSS Flex 布局 <small>90% 的布局场景</small></h2>
  <div class="card">
<pre>/* 父容器（flex container）*/
.container {
  display: flex;
  flex-direction: row;            /* row 横排 | column 竖排 */
  justify-content: center;        /* 主轴：flex-start | center | space-between | space-around */
  align-items: center;            /* 交叉轴：flex-start | center | stretch */
  gap: 12px;                      /* 子元素间距（推荐，替代 margin） */
  flex-wrap: wrap;                /* 放不下时换行 */
}

/* 子元素（flex item）*/
.item {
  flex: 1;                        /* 平分剩余空间 */
  flex: 0 0 120px;                /* 固定 120px 不伸缩 */
  align-self: flex-end;           /* 单独改自己的交叉轴对齐 */
}</pre>
  </div>
  <h3>三行经典布局</h3>
  <div class="grid">
    <div class="card">
      <b class="t">任何东西居中（水平+垂直）</b>
<pre>body {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}</pre>
    </div>
    <div class="card">
      <b class="t">页头 - 内容 - 页脚 满屏布局</b>
<pre>body {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
main { flex: 1; }  /* 中间吃掉剩余高度 */</pre>
    </div>
  </div>
</section>

<!-- ============ CSS 常用 ============ -->
<section id="css-common">
  <h2><span class="ico">🎨</span>CSS 常用属性 <small>颜色 / 字体 / 动效</small></h2>
  <div class="grid">
    <div class="card">
      <b class="t">高频属性</b>
<pre>color: #333;                  /* 文字色 */
background: #f5f5f5;
background: linear-gradient(135deg,#a,#b);
font-size: 15px;
font-weight: 600;             /* 400常规 700粗 */
line-height: 1.7;             /* 行高（倍数最佳） */
text-align: center;
opacity: 0.8;
box-shadow: 0 4px 12px rgba(0,0,0,.1);
transition: all .2s;          /* 平滑变化 */
cursor: pointer;</pre>
    </div>
    <div class="card">
      <b class="t">状态与响应式</b>
<pre>/* 三大伪类 */
a:hover { color: red; }        /* 悬停 */
input:focus { border-color: blue; }
li:last-child { border: none; }

/* 手机适配：窄屏时改成单列 */
@media (max-width: 640px) {
  .grid { grid-template-columns: 1fr; }
}

/* 隐藏 */
display: none;    /* 不占位 */
visibility: hidden; /* 占位不可见 */</pre>
    </div>
  </div>
</section>

<!-- ============ JS 语法 ============ -->
<section id="js-syntax">
  <h2><span class="ico">⚡</span>JS 语法核心 <small>行为层</small></h2>
  <div class="grid">
    <div class="card">
      <b class="t">变量 / 类型 / 流程</b>
<pre>let x = 1;            // 可变
const PI = 3.14;      // 不可变

"str" / 42 / true / null / undefined
[1,2,3]               // 数组
{name: "李", age: 20} // 对象

`模板字符串 ${x}`      // 反引号！

if (a > b) {} else if {} else {}
for (let i = 0; i &lt; n; i++) {}
arr.forEach(item =&gt; {})

function add(a, b) { return a+b; }
const add2 = (a, b) =&gt; a + b;  // 箭头函数</pre>
    </div>
    <div class="card">
      <b class="t">类型转换 / 判断</b>
<pre>Number("3.14")   // 字符串→数字
parseFloat("12.5元")  // → 12.5
String(42)       // 数字→字符串
isNaN(x)         // 是否非数字

// 安全读用户输入
const n = parseFloat(input.value);
if (isNaN(n) || n &lt;= 0) return;

=== 与 ==        // 永远用 ===（不转型比较）
!true / &amp;&amp; / ||  // 非与或
x ?? fallback    // null/undefined 时用 fallback</pre>
    </div>
  </div>
</section>

<!-- ============ JS DOM ============ -->
<section id="js-dom">
  <h2><span class="ico">🖱</span>JS 操作页面（DOM）<small>最有用的一节</small></h2>
  <div class="card">
<pre>// ── 找元素 ──
document.getElementById("id")
document.querySelector(".class / #id / div>p")  // 首个
document.querySelectorAll("li")                  // 全部（NodeList）

// ── 改内容 / 属性 / 样式 ──
el.textContent = "纯文本";
el.innerHTML = "&lt;b&gt;含HTML&lt;/b&gt;";      // 谨防 XSS，别拼用户输入
el.value = "输入框的值";
el.src = "a.png"; el.href = "https://…";
el.style.color = "red";               // 改单个样式
el.classList.add("on");               // 改 class（推荐）
el.classList.toggle("done");          // 有则删无则加

// ── 增删元素 ──
const li = document.createElement("li");
li.textContent = "新项";
ul.appendChild(li);                   // 添加到末尾
el.remove();                          // 删除

// ── 事件（推荐写法）──
btn.addEventListener("click", () =&gt; { … });
input.addEventListener("input", e =&gt; console.log(e.target.value));
form.addEventListener("submit", e =&gt; {
  e.preventDefault();                 // 阻止页面刷新！
});
document.addEventListener("keydown", e =&gt; {
  if (e.key === "Enter") …
});</pre>
  </div>
</section>

<!-- ============ JS 数组 ============ -->
<section id="js-array">
  <h2><span class="ico">📚</span>JS 数组方法 <small>处理数据全靠它们</small></h2>
  <div class="grid">
    <div class="card">
      <b class="t">增删与查找</b>
<pre>const a = [1, 2, 3];
a.push(4);        // 尾加 → 4
a.unshift(0);     // 头加
a.pop();          // 尾删
a.shift();        // 头删
a.splice(1, 1);   // 从下标1删1个
a.indexOf(2);     // 找下标，没有则 -1
a.includes(2);    // 是否包含 → true</pre>
    </div>
    <div class="card">
      <b class="t">变换（不会改原数组）</b>
<pre>const a = [1, 2, 3, 4];

a.map(x =&gt; x * 2)        // [2,4,6,8] 逐个变换
a.filter(x =&gt; x &gt; 2)     // [3,4] 筛选
a.reduce((s, x) =&gt; s+x, 0) // 10 累计
a.find(x =&gt; x &gt; 2)       // 3 第一个满足
a.sort((x, y) =&gt; y - x)  // 降序
[...a, 5]                // 展开：[1,2,3,4,5]
JSON.stringify(a)        // → "[1,2,3,4]"
JSON.parse("[1,2]")      // 字符串 → 数组</pre>
    </div>
  </div>
</section>

<!-- ============ 常见坑 ============ -->
<section id="gotchas">
  <h2><span class="ico">🕳</span>常见坑速排 <small>被坑过才知道系列</small></h2>
  <table>
    <tr><th>症状</th><th>原因</th><th>解法</th></tr>
    <tr><td>JS 报 <code>Cannot read null</code></td><td>脚本在元素之前执行</td><td>script 放 body 末尾，或用 <code>defer</code> 属性</td></tr>
    <tr><td>点了按钮页面刷新、数据没了</td><td>表单默认提交行为</td><td>submit 事件里先 <code>e.preventDefault()</code></td></tr>
    <tr><td><code>0.1+0.2 !== 0.3</code></td><td>浮点精度</td><td>金额用分为单位算，或 <code>.toFixed(2)</code> 展示</td></tr>
    <tr><td>样式写了没生效</td><td>优先级不够 / 被覆盖</td><td>F12 看元素，检查划线项；提高选择器特异性</td></tr>
    <tr><td>flex 子元素宽度失控</td><td>默认可收缩</td><td>子元素加 <code>flex-shrink: 0</code> 或 <code>min-width</code></td></tr>
    <tr><td><code>==</code> 判断出鬼</td><td>隐式类型转换</td><td>永远用 <code>===</code></td></tr>
    <tr><td>手机上字太小</td><td>没设 viewport</td><td>head 里加 <code>&lt;meta name="viewport" …&gt;</code></td></tr>
    <tr><td>localStorage 存对象报错</td><td>只能存字符串</td><td>存 <code>JSON.stringify(obj)</code>，读 <code>JSON.parse(s)</code></td></tr>
  </table>
</section>

<footer>速查手册 · 忘了就来查 · 配合前两套文档使用效果最佳</footer>
</div>
</body>
</html>
