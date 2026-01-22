import { useState, useMemo } from 'react';
import { ArrowUpCircle, ArrowDownCircle, Search, Filter, X, ArrowUpDown, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface Transaction {
  date: string;
  description: string;
  amount: number;
  type: string;
  category?: string;
}

interface TransactionTableProps {
  transactions: Transaction[];
  currency: string;
  limit?: number;
  pageSize?: number;
}

export function TransactionTable({ transactions, currency, limit, pageSize }: TransactionTableProps) {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'credit' | 'debit'>('all');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedTx, setSelectedTx] = useState<Transaction | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const filteredTransactions = useMemo(() => {
    const result = transactions.filter(t => {
      const matchesSearch = t.description.toLowerCase().includes(search.toLowerCase()) || 
                           (t.category?.toLowerCase() || '').includes(search.toLowerCase());
      const matchesType = filterType === 'all' || t.type === filterType;
      return matchesSearch && matchesType;
    });

    // Apply Sorting
    result.sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
    });

    return result;
  }, [transactions, search, filterType, sortOrder]);

  const paginatedTransactions = useMemo(() => {
    if (limit) {
      return filteredTransactions.slice(0, limit);
    }
    if (pageSize) {
      const start = (currentPage - 1) * pageSize;
      return filteredTransactions.slice(start, start + pageSize);
    }
    return filteredTransactions;
  }, [filteredTransactions, limit, pageSize, currentPage]);

  const totalPages = pageSize ? Math.ceil(filteredTransactions.length / pageSize) : 1;

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(prev => prev + 1);
  };

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(prev => prev - 1);
  };

  const toggleSort = () => {
    setSortOrder(prev => prev === 'desc' ? 'asc' : 'desc');
  };

  return (
    <div className="bg-card border border-border rounded-3xl shadow-sm overflow-hidden flex flex-col">
      <div className="p-6 border-b border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-xl font-bold">Transaction History</h3>
          <p className="text-xs text-muted-foreground mt-1 font-medium bg-secondary/50 inline-block px-2 py-0.5 rounded-lg">
            Showing {filteredTransactions.length} of {transactions.length}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground group-focus-within:text-primary transition-colors" />
            <input 
              type="text" 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search history..." 
              className="pl-10 pr-4 py-2 bg-secondary/50 border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-full md:w-64"
            />
          </div>
          
          <button 
            onClick={toggleSort}
            className="flex items-center gap-2 p-2 px-3 border border-border rounded-xl hover:bg-secondary transition-colors text-xs font-bold uppercase tracking-wider text-muted-foreground"
            title="Sort by Date"
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
            {sortOrder === 'desc' ? 'Newest' : 'Oldest'}
          </button>

          <div className="relative">
            <button 
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              className={cn(
                "p-2 border rounded-xl transition-all flex items-center gap-2 text-sm font-medium px-4",
                isFilterOpen || filterType !== 'all' ? "bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/20" : "border-border hover:bg-secondary text-muted-foreground"
              )}
            >
              <Filter className="w-4 h-4" />
              <span className="hidden md:inline">{filterType === 'all' ? 'Filter' : filterType.charAt(0).toUpperCase() + filterType.slice(1)}</span>
            </button>

            <AnimatePresence>
              {isFilterOpen && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setIsFilterOpen(false)} />
                  <motion.div 
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 mt-2 w-40 bg-card border border-border rounded-2xl shadow-xl z-50 overflow-hidden"
                  >
                    <div className="p-1">
                      {(['all', 'credit', 'debit'] as const).map((type) => (
                        <button
                          key={type}
                          onClick={() => {
                            setFilterType(type);
                            setIsFilterOpen(false);
                          }}
                          className={cn(
                            "w-full text-left px-4 py-2.5 text-[10px] font-black uppercase tracking-widest rounded-xl transition-colors",
                            filterType === type ? "bg-primary/10 text-primary" : "hover:bg-secondary text-muted-foreground"
                          )}
                        >
                          {type}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
          
          {(search || filterType !== 'all') && (
            <button 
              onClick={() => {
                setSearch('');
                setFilterType('all');
              }}
              className="p-2 text-rose-500 hover:bg-rose-500/10 rounded-xl transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          {pageSize && filteredTransactions.length > pageSize && (
            <div className="flex items-center gap-3 ml-2 pl-4 border-l border-border">
              <p className="text-[10px] text-muted-foreground font-black uppercase tracking-widest whitespace-nowrap">
                {Math.min((currentPage - 1) * pageSize + 1, filteredTransactions.length)}-{Math.min(currentPage * pageSize, filteredTransactions.length)} of {filteredTransactions.length}
              </p>
              <div className="flex items-center gap-1">
                <button 
                  onClick={handlePrevPage}
                  disabled={currentPage === 1}
                  className="p-1.5 border border-border rounded-lg hover:bg-secondary disabled:opacity-30 transition-colors"
                  title="Previous Page"
                >
                  <ChevronUp className="w-3.5 h-3.5 rotate-[270deg]" />
                </button>
                <button 
                  onClick={handleNextPage}
                  disabled={currentPage === totalPages}
                  className="p-1.5 border border-border rounded-lg hover:bg-secondary disabled:opacity-30 transition-colors"
                  title="Next Page"
                >
                  <ChevronDown className="w-3.5 h-3.5 rotate-[270deg]" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-secondary/30 text-muted-foreground text-[10px] uppercase tracking-[0.2em]">
              <th className="px-6 py-4 font-bold">
                <button onClick={toggleSort} className="flex items-center gap-1 hover:text-primary transition-colors">
                  Date & Description
                  {sortOrder === 'desc' ? <ChevronDown className="w-3 h-3" /> : <ChevronUp className="w-3 h-3" />}
                </button>
              </th>
              <th className="px-6 py-4 font-bold">Category</th>
              <th className="px-6 py-4 font-bold text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {paginatedTransactions.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-6 py-20 text-center">
                  <div className="flex flex-col items-center gap-2 opacity-40">
                    <Search className="w-8 h-8" />
                    <p className="font-bold text-sm">No transactions match your criteria</p>
                  </div>
                </td>
              </tr>
            ) : (
              paginatedTransactions.map((t, i) => (
                <tr key={i} onClick={() => setSelectedTx(t)} className="hover:bg-secondary/20 transition-colors group cursor-pointer">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-4">
                      <div className={cn(
                        "w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 border transition-transform group-hover:scale-110",
                        t.type === 'credit' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-rose-500/10 text-rose-500 border-rose-500/20"
                      )}>
                        {t.type === 'credit' ? <ArrowUpCircle className="w-5 h-5" /> : <ArrowDownCircle className="w-5 h-5" />}
                      </div>
                      <div className="min-w-0">
                        <p className="font-bold text-sm truncate max-w-[200px] md:max-w-xs">{t.description}</p>
                        <p className="text-[10px] text-muted-foreground font-black uppercase mt-1 tracking-tighter">
                          {new Date(t.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-3 py-1.5 rounded-xl text-[10px] font-black bg-secondary border border-border uppercase tracking-widest text-muted-foreground group-hover:border-primary/20 group-hover:text-primary transition-colors">
                      {t.category || 'Uncategorized'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className={cn(
                      "font-black text-sm",
                      t.type === 'credit' ? "text-emerald-500" : "text-foreground"
                    )}>
                      {t.type === 'debit' ? '-' : '+'}{currency} {t.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                    <div className="flex items-center justify-end gap-1.5 mt-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                      <p className="text-[9px] text-muted-foreground font-black uppercase tracking-widest">Settled</p>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      <AnimatePresence>
        {selectedTx && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ opacity: 0 }} 
              animate={{ opacity: 1 }} 
              exit={{ opacity: 0 }} 
              onClick={() => setSelectedTx(null)} 
              className="absolute inset-0 bg-background/80 backdrop-blur-sm" 
            />
            
            <motion.div 
              initial={{ scale: 0.95, opacity: 0, y: 20 }} 
              animate={{ scale: 1, opacity: 1, y: 0 }} 
              exit={{ scale: 0.95, opacity: 0, y: 20 }} 
              className="relative w-full max-w-md bg-card border border-border rounded-[2rem] shadow-2xl overflow-hidden z-10"
            >
                <div className="bg-gradient-to-r from-primary/5 to-secondary/20 p-8 pb-10 border-b border-border/50 text-center relative">
                    <button onClick={() => setSelectedTx(null)} className="absolute top-4 right-4 p-2 hover:bg-black/5 dark:hover:bg-white/5 rounded-full transition-colors">
                      <X className="w-5 h-5 text-muted-foreground" />
                    </button>
                    <span className={cn(
                      "inline-block px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest mb-4 border",
                      selectedTx.type === 'credit' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-rose-500/10 text-rose-500 border-rose-500/20"
                    )}>
                      {selectedTx.type}
                    </span>
                    <h3 className="text-4xl font-black text-foreground mb-2 tracking-tight">
                      {selectedTx.type === 'debit' ? '-' : '+'}{currency}{selectedTx.amount.toLocaleString()}
                    </h3>
                    <p className="text-sm font-bold text-muted-foreground uppercase tracking-wider">
                      {new Date(selectedTx.date).toLocaleDateString(undefined, { dateStyle: 'long' })}
                    </p>
                </div>
                
                <div className="p-8 space-y-6">
                     <div>
                        <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] mb-2 block pl-1">Description</label>
                        <p className="text-lg font-medium leading-relaxed bg-secondary/30 p-5 rounded-2xl border border-border/40 text-foreground/90">
                          {selectedTx.description}
                        </p>
                     </div>
                     
                     <div className="grid grid-cols-2 gap-4">
                         <div className="p-5 bg-secondary/20 rounded-2xl border border-border/40">
                            <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] mb-1 block">Category</label>
                            <p className="font-bold text-sm capitalize">{selectedTx.category || 'Uncategorized'}</p>
                         </div>
                         <div className="p-5 bg-secondary/20 rounded-2xl border border-border/40">
                            <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] mb-1 block">Status</label>
                            <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
                                <p className="font-bold text-sm">Settled</p>
                            </div>
                         </div>
                     </div>
                </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
