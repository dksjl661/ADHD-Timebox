# TIME BOX Frontend

基于 Next.js + Tailwind CSS + TypeScript 的时间盒应用前端。

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 运行开发服务器

```bash
npm run dev
```

应用将在 [http://localhost:3000](http://localhost:3000) 启动。

### 3. 构建生产版本

```bash
npm run build
npm start
```

## 技术栈

- **Next.js 14** - React 框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **Lucide React** - 图标库

## 项目结构

```
iaz/
├── app/
│   ├── layout.tsx      # 根布局
│   ├── page.tsx        # 主页面组件
│   └── globals.css     # 全局样式
├── package.json        # 依赖配置
├── tsconfig.json       # TypeScript 配置
├── tailwind.config.ts  # Tailwind 配置
└── next.config.js      # Next.js 配置
```

## 功能特性

- ✅ 任务管理（添加、优先级设置）
- ✅ 时间盒选择（15/30/60 分钟）
- ✅ 专注模式（倒计时、进度显示）
- ✅ 快速笔记（记录干扰想法）
- ✅ 完成确认（标记完成、继续工作、暂停）

## 类型安全

所有组件和函数都已添加完整的 TypeScript 类型定义，确保代码的类型安全。
