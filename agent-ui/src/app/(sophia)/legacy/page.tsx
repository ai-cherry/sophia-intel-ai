import Link from 'next/link'

const links = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/chat', label: 'Chat' },
  { href: '/insights', label: 'Insights' },
  { href: '/pipeline', label: 'Pipeline' },
  { href: '/teams', label: 'Teams' },
  { href: '/integrations', label: 'Integrations' },
  { href: '/analytics', label: 'Analytics' },
  { href: '/notifications', label: 'Alerts' },
  { href: '/project-management', label: 'Project Management' },
  { href: '/artemis', label: 'Artemis Command Center' },
]

export default function LegacyIndex() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">Legacy Pages</h1>
      <p className="text-sm text-gray-500 mb-4">These routes are retained temporarily for validation and parity checks.</p>
      <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        {links.map((l) => (
          <li key={l.href}>
            <Link className="text-blue-600 hover:underline" href={l.href}>{l.label}</Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

