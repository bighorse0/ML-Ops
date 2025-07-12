import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Database, 
  Activity, 
  GitBranch, 
  Settings,
  Menu
} from 'lucide-react'
import { useState } from 'react'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Features', href: '/features', icon: Database },
  { name: 'Monitoring', href: '/monitoring', icon: Activity },
  { name: 'Lineage', href: '/lineage', icon: GitBranch },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className={`bg-card border-r transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}>
      <div className="flex h-16 items-center justify-between px-4 border-b">
        {!collapsed && (
          <h1 className="text-xl font-bold">Feature Store</h1>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-md hover:bg-accent"
        >
          <Menu size={20} />
        </button>
      </div>
      
      <nav className="p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                `flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                }`
              }
            >
              <Icon size={20} className="mr-3" />
              {!collapsed && item.name}
            </NavLink>
          )
        })}
      </nav>
    </div>
  )
} 