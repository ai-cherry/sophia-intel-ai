import { useTheme } from '../../hooks/useTheme'
import { Menu } from '@headlessui/react'

export default function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme()

  const themes = [
    { value: 'light', label: '☀️ Light', icon: '☀️' },
    { value: 'dark', label: '🌙 Dark', icon: '🌙' },
    { value: 'system', label: '💻 System', icon: '💻' }
  ] as const

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="p-2 rounded-lg bg-card hover:bg-card-hover border border-custom transition-colors">
        <span className="text-xl">
          {theme === 'system' ? '💻' : resolvedTheme === 'dark' ? '🌙' : '☀️'}
        </span>
      </Menu.Button>

      <Menu.Items className="absolute right-0 mt-2 w-36 origin-top-right rounded-lg bg-card border border-custom shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
        <div className="py-1">
          {themes.map((item) => (
            <Menu.Item key={item.value}>
              {({ active }) => (
                <button
                  onClick={() => setTheme(item.value)}
                  className={`${
                    active ? 'bg-card-hover' : ''
                  } ${
                    theme === item.value ? 'text-accent' : 'text-primary'
                  } group flex w-full items-center px-3 py-2 text-sm transition-colors`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                  {theme === item.value && (
                    <span className="ml-auto text-accent">✓</span>
                  )}
                </button>
              )}
            </Menu.Item>
          ))}
        </div>
      </Menu.Items>
    </Menu>
  )
}