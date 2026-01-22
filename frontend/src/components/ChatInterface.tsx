import { useState, useRef, useEffect } from 'react';
import { User, Bot, Sparkles, ArrowUp, ArrowDown } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import type { Message } from '../App';

interface ChatInterfaceProps {
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
}

export function ChatInterface({ messages, setMessages }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollButton(!isBottom);
    }
  };

  const scrollToBottom = () => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          history: messages.map(m => ({ role: m.role === 'bot' ? 'assistant' : 'user', content: m.content })),
          context: 'FINANCIAL_AI_PAGE'
        })
      });

      if (!response.ok) throw new Error("Agent failed to respond.");

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'bot', content: data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'bot', content: "I'm sorry, I'm having trouble connecting to the financial agent right now." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] bg-background relative">
      
      {/* Messages Area - Centered Column */}
      <div 
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto custom-scrollbar w-full"
      >
        <div className="max-w-3xl mx-auto w-full px-4 pt-8 pb-32 min-h-full flex flex-col">
          
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center space-y-10 my-auto">
               <div className="w-16 h-16 bg-foreground/5 rounded-2xl flex items-center justify-center mb-4">
                  <Sparkles className="w-8 h-8 text-foreground/80" />
               </div>
               
               <div className="space-y-4 max-w-lg">
                  <h2 className="text-3xl font-medium tracking-tight text-foreground">
                    Hello, User
                  </h2>
                  <h3 className="text-2xl font-light text-muted-foreground">
                    How can I help analyze your finances today?
                  </h3>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl mt-12">
                  {[
                    "Summarize my total spending",
                    "Show me the largest transactions",
                    "What are my monthly trends?",
                    "How much did I spend on Food?"
                  ].map((q, i) => (
                    <button 
                      key={i}
                      onClick={() => setInput(q)}
                      className="text-left p-4 rounded-xl bg-secondary/30 hover:bg-secondary/60 border border-border/40 hover:border-border transition-all text-sm text-foreground/80"
                    >
                      {q}
                    </button>
                  ))}
               </div>
            </div>
          ) : (
            <div className="space-y-8 py-4">
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "flex gap-6 w-full",
                    m.role === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  {m.role === 'bot' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary/80 to-primary flex items-center justify-center shrink-0 shadow-sm mt-1">
                      <Bot className="w-4 h-4 text-primary-foreground" />
                    </div>
                  )}
                  
                  <div className={cn(
                    "relative max-w-[90%] lg:max-w-[85%]",
                    m.role === 'user' ? "bg-secondary/80 text-foreground px-5 py-3.5 rounded-3xl rounded-tr-sm" : "text-foreground leading-7"
                  )}>
                    <div className="prose prose-neutral dark:prose-invert max-w-none text-base">
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ ...props }) => <p className="mb-4 last:mb-0 leading-relaxed text-foreground/90" {...props} />,
                          ul: ({ ...props }) => <ul className="list-disc pl-5 mb-4 space-y-2 text-foreground/90" {...props} />,
                          ol: ({ ...props }) => <ol className="list-decimal pl-5 mb-4 space-y-2 text-foreground/90" {...props} />,
                          li: ({ ...props }) => <li className="pl-1" {...props} />,
                          h1: ({ ...props }) => <h1 className="text-2xl font-bold text-foreground mb-4 mt-8 pb-2 border-b border-border/40" {...props} />,
                          h2: ({ ...props }) => <h2 className="text-xl font-semibold text-foreground/95 mb-3 mt-6" {...props} />,
                          h3: ({ ...props }) => <h3 className="text-lg font-medium text-foreground/90 mb-2 mt-4" {...props} />,
                          table: ({ ...props }) => (
                            <div className="overflow-hidden my-6 rounded-xl border border-border/60 shadow-sm bg-card/30">
                              <table className="w-full text-sm text-left" {...props} />
                            </div>
                          ),
                          thead: ({ ...props }) => <thead className="bg-secondary/50 text-muted-foreground uppercase text-xs font-semibold tracking-wider" {...props} />,
                          tr: ({ ...props }) => <tr className="border-b border-border/40 last:border-0 hover:bg-muted/20 transition-colors" {...props} />,
                          th: ({ ...props }) => <th className="px-6 py-4 font-medium" {...props} />,
                          td: ({ ...props }) => <td className="px-6 py-4 align-top text-foreground/80" {...props} />,
                          strong: ({ ...props }) => <strong className="font-bold text-foreground" {...props} />,
                          a: ({ ...props }) => <a className="text-primary hover:underline font-medium underline-offset-4" target="_blank" rel="noopener noreferrer" {...props} />,
                          blockquote: ({ ...props }) => <blockquote className="border-l-4 border-primary/40 bg-secondary/10 pl-5 py-3 my-4 italic text-muted-foreground rounded-r-lg" {...props} />,
                          hr: ({ ...props }) => <hr className="my-8 border-border/60" {...props} />,
                          pre: ({ ...props }) => <pre className="bg-secondary/40 p-4 rounded-xl overflow-x-auto my-4 text-xs border border-border/30" {...props} />,
                          code: ({ inline, ...props }: { inline?: boolean, [key: string]: any }) => (
                            <code 
                              className={inline 
                                ? "bg-secondary/60 px-1.5 py-0.5 rounded text-sm font-mono text-primary-foreground/90 bg-primary/10" 
                                : "bg-transparent text-sm font-mono text-foreground"
                              } 
                              {...props} 
                            />
                          ),
                        }}
                      >
                        {m.content}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {m.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0 mt-1">
                      <User className="w-4 h-4 text-muted-foreground" />
                    </div>
                  )}
                </motion.div>
              ))}
              
              {isLoading && (
                <div className="flex gap-6 w-full">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary/80 to-primary flex items-center justify-center shrink-0 animate-pulse">
                    <Sparkles className="w-4 h-4 text-primary-foreground" />
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground mt-2">
                    <span className="w-2 h-2 bg-foreground/20 rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-foreground/20 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-2 h-2 bg-foreground/20 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  </div>
                </div>
              )}
              <div ref={scrollRef} />
            </div>
          )}
          
          {/* Scroll to Bottom Button */}
          {showScrollButton && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={scrollToBottom}
              className="fixed bottom-32 left-1/2 -translate-x-1/2 z-50 p-2 bg-primary/90 text-primary-foreground rounded-full shadow-lg hover:bg-primary transition-colors backdrop-blur-sm border border-primary/20"
            >
              <ArrowDown className="w-5 h-5" />
            </motion.button>
          )}
        </div>
      </div>

      {/* Input Area - Floating at bottom */}
      <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-background via-background to-transparent pt-10 pb-8 px-4">
        <div className="max-w-3xl mx-auto relative">
          <div className="relative flex items-end gap-2 bg-secondary/40 border border-border/50 rounded-[1.5rem] p-2 pl-4 shadow-lg backdrop-blur-md focus-within:bg-secondary/60 focus-within:border-primary/30 transition-all">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if(e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
              placeholder="Message Financial AI..."
              className="w-full bg-transparent border-none focus:ring-0 resize-none max-h-32 py-3 text-base custom-scrollbar"
              rows={1}
              style={{ minHeight: '44px' }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="p-2.5 bg-primary text-primary-foreground rounded-full disabled:opacity-50 disabled:bg-muted hover:opacity-90 transition-all mb-0.5"
            >
              <ArrowUp className="w-5 h-5" />
            </button>
          </div>
          <p className="text-xs text-center text-muted-foreground/50 mt-3">
             Financial AI can make mistakes. Please check important info.
          </p>
        </div>
      </div>
    </div>
  );
}

