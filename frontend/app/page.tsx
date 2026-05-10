import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4">iPerson</h1>
      <p className="text-xl mb-8">AI-Powered Personal IP Operation Platform</p>
      <div className="flex gap-4">
        <Link href="/login" className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          登录
        </Link>
        <Link href="/dashboard" className="px-6 py-3 bg-gray-200 rounded-lg hover:bg-gray-300">
          控制台
        </Link>
      </div>
    </main>
  )
}