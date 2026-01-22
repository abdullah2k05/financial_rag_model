import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { motion } from 'framer-motion';
import { TrendingDown, ShoppingBag, Zap, Target, Award } from 'lucide-react';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

interface ChartsProps {
  spendingData: Record<string, number>;
  trendData: Record<string, { income: number; expense: number }>;
  merchantData?: { name: string; value: number }[];
  currency: string;
}

export function Charts({ spendingData, trendData, merchantData = [], currency }: ChartsProps) {
  const pieData = Object.entries(spendingData).map(([name, value]) => ({ name, value }));
  
  const barData = Object.entries(trendData).map(([month, values]) => ({
    month: new Date(month + "-01").toLocaleDateString('en-US', { month: 'short' }),
    income: values.income,
    expense: values.expense
  }));

  const maxMerchantValue = Math.max(...merchantData.map(m => m.value), 0);

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Cash Flow Trends */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-card border border-border rounded-[2.5rem] p-6 md:p-8 shadow-sm h-[420px] relative overflow-hidden group"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-3xl -mr-16 -mt-16 group-hover:bg-primary/10 transition-colors" />
          <div className="flex items-center justify-between mb-8 relative z-10">
             <div className="space-y-1">
                <h3 className="text-lg font-bold">Monthly Balance</h3>
                <p className="text-[10px] text-muted-foreground font-black uppercase tracking-widest">Cash flow dynamics</p>
             </div>
             <div className="flex items-center gap-4 text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span> In</div>
                <div className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span> Out</div>
             </div>
          </div>
          <div className="w-full h-[280px] relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" opacity={0.3} />
                <XAxis 
                  dataKey="month" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 10, fontWeight: 700, fill: 'hsl(var(--muted-foreground))' }} 
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 10, fontWeight: 700, fill: 'hsl(var(--muted-foreground))' }}
                  tickFormatter={(v) => `${v >= 1000 ? (v/1000).toFixed(0) + 'k' : v}`}
                />
                <Tooltip 
                   cursor={{ fill: 'hsl(var(--secondary)/0.3)', radius: 12 }}
                   contentStyle={{ 
                     backgroundColor: 'hsl(var(--card))', 
                     borderColor: 'hsl(var(--border))',
                     borderRadius: '20px',
                     boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.15)',
                     border: '1px solid hsl(var(--border))',
                     padding: '12px'
                   }}
                />
                <Bar dataKey="income" fill="#10b981" radius={[8, 8, 4, 4]} barSize={20} />
                <Bar dataKey="expense" fill="#ef4444" radius={[8, 8, 4, 4]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Category Distribution */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-card border border-border rounded-[2.5rem] p-6 md:p-8 shadow-sm h-[420px] group overflow-hidden"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="space-y-1">
              <h3 className="text-lg font-bold">Category Distribution</h3>
              <p className="text-[10px] text-muted-foreground font-black uppercase tracking-widest">Spending habits</p>
            </div>
          </div>
          <div className="flex-1 w-full h-[300px] relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={85}
                  outerRadius={115}
                  paddingAngle={8}
                  dataKey="value"
                  stroke="none"
                  cornerRadius={12}
                >
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} className="hover:opacity-80 transition-opacity cursor-pointer" />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--card))', 
                    borderColor: 'hsl(var(--border))',
                    borderRadius: '20px',
                    boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.15)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
               <motion.div 
                 animate={{ rotate: [0, 10, -10, 0] }}
                 transition={{ repeat: Infinity, duration: 4 }}
               >
                 <Zap className="w-6 h-6 text-primary mb-1 fill-primary/10" />
               </motion.div>
               <span className="text-[10px] font-black text-primary uppercase tracking-[0.3em]">Insights</span>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Top Spending Entities - FUTURISTIC LEADERBOARD */}
      <motion.div
         initial={{ opacity: 0, y: 30 }}
         animate={{ opacity: 1, y: 0 }}
         transition={{ delay: 0.3 }}
         className="relative group"
      >
        <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 via-primary/5 to-transparent rounded-[3rem] blur-2xl opacity-50 group-hover:opacity-100 transition duration-1000" />
        <div className="relative bg-card border border-border rounded-[3rem] overflow-hidden shadow-2xl backdrop-blur-3xl">
          <div className="p-10 border-b border-border bg-gradient-to-b from-secondary/20 to-transparent flex flex-wrap items-center justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="w-16 h-16 bg-primary/10 rounded-[2rem] flex items-center justify-center border border-primary/20 shadow-inner">
                 <Award className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h3 className="text-2xl font-black tracking-tight">Financial Powerhouses</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  <p className="text-[10px] text-muted-foreground font-black uppercase tracking-[0.2em]">Live Analysis of your biggest spend providers</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
               <div className="px-4 py-2 bg-secondary/50 rounded-2xl border border-border">
                  <span className="text-[9px] font-black text-muted-foreground uppercase block mb-0.5 tracking-widest">Total Monitored</span>
                  <span className="text-sm font-black">{merchantData.length} Entities</span>
               </div>
            </div>
          </div>

          <div className="p-10 grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
            {merchantData.length > 0 ? merchantData.map((merchant, idx) => (
              <motion.div 
                key={merchant.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + idx * 0.1 }}
                className="relative group/item"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-5">
                    <div className="relative">
                      <div className="absolute inset-0 bg-primary/20 blur-md rounded-2xl scale-0 group-hover/item:scale-110 transition-transform" />
                      <div className="w-14 h-14 rounded-2xl bg-secondary/50 border border-border flex items-center justify-center text-xl font-black text-primary relative z-10 group-hover/item:border-primary/30 transition-colors">
                        {merchant.name.charAt(0)}
                      </div>
                      <div className="absolute -top-1 -right-1 w-5 h-5 bg-primary rounded-full flex items-center justify-center text-[8px] font-black text-primary-foreground border-2 border-card z-20">
                        {idx + 1}
                      </div>
                    </div>
                    <div className="min-w-0">
                      <h4 className="font-black text-sm uppercase tracking-wider truncate max-w-[150px] lg:max-w-[200px]">{merchant.name}</h4>
                      <p className="text-[9px] font-bold text-muted-foreground mt-1 flex items-center gap-1.5">
                        <Target className="w-3 h-3 text-primary/60" />
                        PRIMARY CATEGORY SOURCE
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-black text-foreground">{currency}{merchant.value.toLocaleString()}</span>
                    <div className="flex items-center justify-end gap-1 mt-1 text-[9px] font-black text-rose-500 uppercase tracking-widest">
                       <TrendingDown className="w-3 h-3" />
                       - {((merchant.value / trendData[Object.keys(trendData)[0]]?.expense || merchant.value) * 10).toFixed(1)}% Month
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 space-y-2">
                  <div className="h-3 w-full bg-secondary/50 rounded-full overflow-hidden border border-border/50">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${(merchant.value / maxMerchantValue) * 100}%` }}
                      transition={{ delay: 0.8 + idx * 0.1, duration: 1.5, ease: [0.22, 1, 0.36, 1] }}
                      className="h-full bg-gradient-to-r from-primary via-primary/80 to-primary/40 rounded-full relative"
                    >
                       <div className="absolute top-0 right-0 h-full w-4 bg-white/20 skew-x-12 animate-[shimmer_2s_infinite]" />
                    </motion.div>
                  </div>
                  <div className="flex justify-between items-center text-[10px] font-black text-muted-foreground/60 uppercase tracking-widest">
                     <span>Contribution to cycle</span>
                     <span>{((merchant.value / maxMerchantValue) * 100).toFixed(0)}% Intensity</span>
                  </div>
                </div>
                
                <div className="absolute inset-x-0 -bottom-4 h-px bg-gradient-to-r from-transparent via-border to-transparent opacity-50 last:hidden" />
              </motion.div>
            )) : (
              <div className="col-span-full py-20 text-center space-y-4">
                 <ShoppingBag className="w-12 h-12 text-muted-foreground mx-auto opacity-20" />
                 <p className="font-black text-muted-foreground/40 uppercase tracking-[0.5em]">System Waiting for Statement Upload</p>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
