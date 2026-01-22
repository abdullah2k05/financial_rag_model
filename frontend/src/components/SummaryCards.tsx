import { TrendingUp, TrendingDown, Wallet, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { motion } from 'framer-motion';

interface SummaryCardsProps {
  data: {
    total_income: number;
    total_expense: number;
    net_balance: number;
    transaction_count: number;
  };
  currency: string;
}

export function SummaryCards({ data, currency }: SummaryCardsProps) {
  const cards = [
    {
      label: 'Net Balance',
      value: data.net_balance,
      icon: Wallet,
      color: 'text-primary',
      bg: 'bg-primary/10',
      trend: data.net_balance >= 0 ? 'up' : 'down'
    },
    {
      label: 'Total Income',
      value: data.total_income,
      icon: TrendingUp,
      color: 'text-emerald-500',
      bg: 'bg-emerald-500/10',
      trend: 'up'
    },
    {
      label: 'Total Spending',
      value: data.total_expense,
      icon: TrendingDown,
      color: 'text-rose-500',
      bg: 'bg-rose-500/10',
      trend: 'down'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {cards.map((card, i) => (
        <motion.div
          key={card.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className="bg-card border border-border rounded-3xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group"
        >
          <div className="flex justify-between items-start mb-4">
            <div className={`${card.bg} p-3 rounded-2xl`}>
              <card.icon className={`w-6 h-6 ${card.color}`} />
            </div>
            {card.trend === 'up' ? (
              <div className="flex items-center gap-1 text-emerald-500 text-xs font-bold bg-emerald-500/10 px-2 py-1 rounded-full">
                <ArrowUpRight className="w-3 h-3" />
                <span>Active</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-rose-500 text-xs font-bold bg-rose-500/10 px-2 py-1 rounded-full">
                <ArrowDownRight className="w-3 h-3" />
                <span>Alert</span>
              </div>
            )}
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{card.label}</p>
            <h3 className="text-3xl font-bold tracking-tight">
              {currency} {card.value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </h3>
          </div>
          
          {/* Subtle background decoration */}
          <div className={`absolute -right-4 -bottom-4 w-24 h-24 rounded-full ${card.bg} blur-2xl opacity-50 group-hover:scale-150 transition-transform duration-500`} />
        </motion.div>
      ))}
    </div>
  );
}
