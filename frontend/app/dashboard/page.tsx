export default function DashboardPage() {
  const navItems = [
    { href: '/dashboard', label: '控制台' },
    { href: '/contents', label: '内容管理' },
    { href: '/personas', label: '人设管理' },
    { href: '/topics', label: '选题库' },
    { href: '/analytics', label: '数据分析' },
    { href: '/settings', label: '设置' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-56 bg-white border-r p-4">
        <h2 className="text-xl font-bold mb-8">iPerson</h2>
        <nav className="space-y-2">
          {navItems.map(item => (
            <a key={item.href} href={item.href}
               className="block px-4 py-2 rounded-lg hover:bg-blue-50 hover:text-blue-600">
              {item.label}
            </a>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="ml-56 p-8">
        <h1 className="text-3xl font-bold mb-6">控制台</h1>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="p-6 bg-white rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-2">已发布内容</h3>
            <p className="text-3xl font-bold text-blue-600">0</p>
          </div>
          <div className="p-6 bg-white rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-2">活跃人设</h3>
            <p className="text-3xl font-bold text-green-600">0</p>
          </div>
          <div className="p-6 bg-white rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-2">总互动</h3>
            <p className="text-3xl font-bold text-purple-600">0</p>
          </div>
        </div>
      </main>
    </div>
  )
}