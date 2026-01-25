import { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { SummaryCards } from './components/SummaryCards';
import { Charts } from './components/Charts';
import { TransactionTable } from './components/TransactionTable';
import { ChatInterface } from './components/ChatInterface';
import { Upload, Loader2, AlertCircle, RefreshCcw, LayoutDashboard, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';


if (!import.meta.env.VITE_API_BASE) {
  throw new Error("VITE_API_BASE is not defined in environment variables");
}
const API_BASE = `${import.meta.env.VITE_API_BASE}/api/v1`;


// Utility function for class names
function cn(...inputs: (string | boolean | undefined | null)[]) {
  return inputs.filter(Boolean).join(' ');
}

interface Transaction {
  date: string;
  description: string;
  amount: number;
  type: string;
  category?: string;
  currency?: string; 
}

export interface Message {
  role: 'user' | 'bot';
  content: string;
}

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Data states
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currency, setCurrency] = useState<string>("USD"); // Default currency
  const [summary, setSummary] = useState({
    total_income: 0,
    total_expense: 0,
    net_balance: 0,
    transaction_count: 0
  });
  const [spending, setSpending] = useState<Record<string, number>>({});
  const [trends, setTrends] = useState<Record<string, { income: number; expense: number }>>({});
  const [merchants, setMerchants] = useState<{ name: string; value: number }[]>([]);

  const fetchData = async () => {
    setIsLoadingData(true);
    try {
      const [summRes, spendRes, trendRes, merchRes, transRes] = await Promise.all([
        fetch(`${API_BASE}/analytics/summary`),
        fetch(`${API_BASE}/analytics/spending`),
        fetch(`${API_BASE}/analytics/trends`),
        fetch(`${API_BASE}/analytics/merchants`),
        fetch(`${API_BASE}/analytics/transactions`)
      ]);

      if (summRes.ok) setSummary(await summRes.json());
      if (spendRes.ok) setSpending(await spendRes.json());
      if (trendRes.ok) setTrends(await trendRes.json());
      if (merchRes.ok) setMerchants(await merchRes.json());
      if (transRes.ok) {
        const transData = await transRes.json();
        setTransactions(transData);
        if (transData.length > 0 && transData[0].currency) {
          setCurrency(transData[0].currency);
        }
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    } finally {
      setIsLoadingData(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = async () => {
    setIsLoadingData(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/analytics/reset`, { method: 'POST' });
      if (!res.ok) {
        throw new Error('Failed to reset dashboard data');
      }
      const emptySummary = await res.json();
      setSummary(emptySummary);
      setTransactions([]);
      setMessages([]);
      setSpending({});
      setTrends({});
      setCurrency('USD');
    } catch (err) {
      console.error('Failed to reset data', err);
      if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setIsLoadingData(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Upload failed");
      }

      const data = await response.json();
      
      // Handle new response structure { transactions, metadata }
      if (data.transactions) {
        setTransactions(data.transactions);
        if (data.metadata?.currency) {
          setCurrency(data.metadata.currency);
        }
      } else {
        // Fallback for array response if API hasn't updated or cached
        setTransactions(data);
      }

      // Refresh analytics after successful upload
      await fetchData();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred during upload.");
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="flex flex-col lg:flex-row min-h-screen bg-background text-foreground font-sans">
      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b border-border bg-card/80 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-2">
           <div className="bg-primary/10 p-1.5 rounded-lg border border-primary/20">
              <LayoutDashboard className="w-5 h-5 text-primary" />
           </div>
           <span className="font-bold text-lg tracking-tight">Money Lens</span>
        </div>
        <button 
          onClick={() => setIsMobileMenuOpen(true)}
          className="p-2 hover:bg-secondary rounded-lg transition-colors"
        >
          <Menu className="w-6 h-6" />
        </button>
      </div>

      {/* Mobile Sidebar Drawer */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileMenuOpen(false)}
              className="fixed inset-0 bg-black/60 z-[60] lg:hidden backdrop-blur-sm"
            />
            <motion.div
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed inset-y-0 left-0 w-[280px] z-[70] lg:hidden bg-background"
            >
              <Sidebar 
                activeTab={activeTab} 
                setActiveTab={setActiveTab} 
                onClose={() => setIsMobileMenuOpen(false)} 
              />
              <button 
                onClick={() => setIsMobileMenuOpen(false)}
                className="absolute top-4 right-4 p-2 bg-secondary/80 rounded-full border border-border"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      </div>
      
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header */}
        <header className="h-20 border-b border-border px-8 flex items-center justify-between glass sticky top-0 z-50">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              {activeTab === 'dashboard' ? 'Financial Overview' : activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
            </h2>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-[0.2em] mt-0.5">
              Welcome back, User
            </p>
          </div>

          <div className="flex items-center gap-4">
            <button 
              onClick={handleRefresh}
              className="p-2 hover:bg-secondary rounded-xl transition-colors"
              title="Reset & Refresh Data"
            >
              <RefreshCcw className={cn("w-5 h-5 text-muted-foreground", isLoadingData && "animate-spin")} />
            </button>
            
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="bg-primary text-primary-foreground px-5 py-2.5 rounded-2xl text-sm font-bold flex items-center gap-2 hover:opacity-90 transition-all shadow-lg shadow-primary/20 disabled:opacity-50"
            >
              {isUploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              {isUploading ? 'Analyzing...' : 'Upload Statement'}
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              accept=".csv,.pdf" 
              onChange={handleFileUpload}
            />
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          {error && (
            <motion.div 
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-8 bg-destructive/10 border border-destructive/20 p-4 rounded-2xl flex items-center gap-3 text-destructive"
            >
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm font-medium">{error}</span>
            </motion.div>
          )}

          <AnimatePresence mode="wait">

            {activeTab === 'dashboard' && (
              <motion.div 
                key="dashboard"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-8"
              >
                <SummaryCards data={summary} currency={currency} />
                
                <section>
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold">Data Visualization</h3>
                    <div className="flex gap-2">
                       <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                       <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Real-time Analysis</span>
                    </div>
                  </div>
                  <Charts spendingData={spending} trendData={trends} merchantData={merchants} currency={currency} />
                </section>

                <section>
                  <TransactionTable transactions={transactions} currency={currency} limit={10} />
                </section>
              </motion.div>
            )}

            {activeTab === 'chat' && (
              <motion.div 
                key="chat"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 h-full -m-8" // Negative margin to counteract main padding, making it full bleed
              >
                <ChatInterface messages={messages} setMessages={setMessages} />
              </motion.div>
            )}

            {activeTab === 'history' && (
              <motion.div 
                key="history"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-8"
              >
                {/* Dynamic Financial Snapshot from AI Agent */}
                <SnapshotCard transactions={transactions} />

                {/* Transactions Table */}
                <TransactionTable transactions={transactions} currency={currency} pageSize={25} />
              </motion.div>
            )}

            {activeTab !== 'dashboard' && activeTab !== 'chat' && activeTab !== 'history' && (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4 py-20">
                <div className="p-6 bg-secondary/50 rounded-full border border-border">
                  <LayoutDashboard className="w-12 h-12 text-muted-foreground" />
                </div>
                <h3 className="text-2xl font-bold">Under Construction</h3>
                <p className="text-muted-foreground max-w-md">
                  This feature is currently being developed. Check back soon!
                </p>
              </div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

// Sub-component for fetching and rendering the snapshot
function SnapshotCard({ transactions }: { transactions: Transaction[] }) {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSnapshot = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE}/chat`, {

          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: 'Get snapshot',
            context: 'TRANSACTIONS_PAGE',
            history: []
          })
        });
        if (res.ok) {
          const data = await res.json();
          setContent(data.response);
        }
      } catch (err) {
        console.error("Failed to fetch snapshot", err);
        setContent("Failed to load financial snapshot.");
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(() => {
        fetchSnapshot();
    }, 500);

    return () => clearTimeout(timer);
  }, [transactions]);

  if (loading) {
    return (
      <div className="bg-card/50 border border-border/50 rounded-[2rem] p-12 shadow-sm flex flex-col items-center justify-center gap-4 text-muted-foreground animate-pulse backdrop-blur-sm">
        <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
        </div>
        <span className="font-medium tracking-wide text-xs uppercase">Analyzing your finances...</span>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-[2.5rem] border border-border/50 bg-gradient-to-b from-card/90 to-card/50 shadow-2xl backdrop-blur-xl transition-all hover:shadow-[0_0_50px_-15px_rgba(124,58,237,0.1)] group">
       {/* Background Effects */}
       <div className="absolute -top-32 -right-32 w-80 h-80 bg-primary/10 blur-[100px] rounded-full pointer-events-none group-hover:bg-primary/15 transition-all duration-700" />
       <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-secondary/20 blur-[100px] rounded-full pointer-events-none" />

       <div className="p-8 md:p-12 relative z-10">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              // Typography
              h1: ({ ...props }) => <h1 className="text-3xl font-black mb-8 pb-4 border-b border-border/30 bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent" {...props} />,
              h2: ({ ...props }) => <h2 className="text-2xl font-bold mb-6 mt-10 first:mt-0 flex items-center gap-3 text-foreground" {...props} />,
              h3: ({ ...props }) => <h3 className="text-lg font-semibold mb-3 mt-6 text-foreground/80" {...props} />,
              p: ({ ...props }) => <p className="mb-4 leading-relaxed text-muted-foreground" {...props} />,
              
              // Lists
              ul: ({ ...props }) => <ul className="space-y-3 mb-6" {...props} />,
              li: ({ ...props }) => <li className="flex items-start gap-2 text-foreground/90 leading-relaxed pl-1" {...props} />,
              
              // Tables
              table: ({ ...props }) => (
                <div className="overflow-hidden my-8 rounded-2xl border border-border/40 shadow-sm bg-card/40">
                  <table className="w-full text-sm text-left" {...props} />
                </div>
              ),
              thead: ({ ...props }) => <thead className="bg-muted/30 text-muted-foreground/80 uppercase text-[10px] font-bold tracking-widest border-b border-border/40" {...props} />,
              tr: ({ ...props }) => <tr className="border-b border-border/40 last:border-0 hover:bg-muted/20 transition-colors group/row" {...props} />,
              th: ({ ...props }) => <th className="px-6 py-4 font-medium" {...props} />,
              td: ({ ...props }) => <td className="px-6 py-4 align-top text-foreground/80 group-hover/row:text-foreground transition-colors" {...props} />,
              
              // Elements
              blockquote: ({ ...props }) => <blockquote className="border-l-4 border-primary/30 bg-primary/5 pl-6 py-4 my-6 italic text-muted-foreground rounded-r-xl" {...props} />,
              strong: ({ ...props }) => <strong className="font-bold text-foreground" {...props} />,
              hr: ({ ...props }) => <hr className="my-8 border-border/40" {...props} />,
            }}
          >
            {content}
          </ReactMarkdown>
       </div>
       
       <div className="bg-muted/5 p-4 border-t border-border/10 flex justify-between items-center backdrop-blur-sm">
           <span className="text-[10px] uppercase tracking-[0.2em] font-bold text-muted-foreground/40 flex items-center gap-2">
             <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
             Live Financial Intelligence
           </span>
           <div className="flex gap-1 opacity-50">
             <div className="w-1 h-1 rounded-full bg-foreground/20"></div>
             <div className="w-1 h-1 rounded-full bg-foreground/20"></div>
           </div>
       </div>
    </div>
  );
}

export default App;
