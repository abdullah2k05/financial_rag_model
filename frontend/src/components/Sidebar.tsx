import { LayoutDashboard, MessageSquare, Settings, PieChart, History, CreditCard } from 'lucide-react';
import { cn } from '../lib/utils';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export function Sidebar({ activeTab, setActiveTab }: SidebarProps) {
  const menuItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'chat', icon: MessageSquare, label: 'Financial AI' },
    { id: 'history', icon: History, label: 'Transactions' },
    { id: 'categories', icon: PieChart, label: 'Spending' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <aside className="w-64 border-r border-border bg-card/50 backdrop-blur-xl h-screen sticky top-0 flex flex-col">
      <div className="p-6 flex items-center gap-3">
        <div className="bg-primary/10 p-2 rounded-xl border border-primary/20">
          <CreditCard className="w-6 h-6 text-primary" />
        </div>
        <span className="font-bold text-xl tracking-tight">Abdullah</span>
      </div>

      <nav className="flex-1 px-4 space-y-2 mt-4">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200",
                isActive 
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20 scale-[1.02]" 
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground hover:translate-x-1"
              )}
            >
              <Icon className={cn("w-5 h-5", isActive ? "text-white" : "text-muted-foreground")} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="p-6 border-t border-border mt-auto">
        <div className="bg-secondary/50 rounded-2xl p-4 border border-border">
          <p className="text-xs text-muted-foreground uppercase font-semibold tracking-wider mb-2">Pro Plan</p>
          <p className="text-xs mb-3">Get advanced spending insights with LLM agents.</p>
          <button className="w-full py-2 bg-foreground text-background text-xs font-bold rounded-lg hover:opacity-90 transition-opacity">
            Upgrade Now
          </button>
        </div>
      </div>
    </aside>
  );
}
