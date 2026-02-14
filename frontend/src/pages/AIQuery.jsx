/**
 * AI Query Page - RAG-powered chat interface
 */
import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Layout } from '../components/Layout';
import { ragAPI, jobsAPI } from '../lib/api';
import { 
  Send, 
  ArrowLeft, 
  Bot, 
  User, 
  FileText,
  Sparkles,
  Loader
} from 'lucide-react';

export const AIQueryPage = () => {
  const { id: jobId } = useParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // Fetch job details
  const { data: job } = useQuery({
    queryKey: ['job', jobId],
    queryFn: async () => {
      const response = await jobsAPI.get(jobId);
      return response.data;
    },
  });

  // Query mutation
  const queryMutation = useMutation({
    mutationFn: async (query) => {
      const chatHistory = messages
        .filter(m => m.role !== 'system')
        .map(m => [m.role === 'user' ? m.content : '', m.role === 'assistant' ? m.content : ''])
        .filter(([q, a]) => q && a);

      const response = await ragAPI.queryJob(jobId, {
        query,
        top_k: 5,
        use_conversation: chatHistory.length > 0,
        chat_history: chatHistory.length > 0 ? chatHistory : undefined,
      });
      return response.data;
    },
    onSuccess: (data, query) => {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          sources: data.sources,
          timestamp: new Date(),
        }
      ]);
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || queryMutation.isPending) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    
    await queryMutation.mutateAsync(input);
  };

  const handleExampleQuery = (query) => {
    setInput(query);
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto h-[calc(100vh-12rem)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate(jobId ? `/jobs/${jobId}` : '/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-6 w-6" />
            </button>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                <Sparkles className="h-6 w-6 mr-2 text-primary-600" />
                AI Query
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                {job ? `Ask questions about ${job.title} candidates` : 'Search across all resumes'}
              </p>
            </div>
          </div>
        </div>

        {/* Chat Container */}
        <div className="flex-1 flex flex-col card overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.length === 0 ? (
              <EmptyState onExampleClick={handleExampleQuery} />
            ) : (
              <>
                {messages.map((message, index) => (
                  <Message key={index} message={message} />
                ))}
                {queryMutation.isPending && (
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                        <Bot className="h-5 w-5 text-primary-600" />
                      </div>
                    </div>
                    <div className="flex-1">
                      <div className="bg-gray-100 rounded-lg p-4">
                        <Loader className="h-5 w-5 animate-spin text-gray-400" />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <form onSubmit={handleSubmit} className="flex items-center space-x-4">
              <div className="flex-1">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                  placeholder="Ask about candidates... (e.g., 'Who has 5+ years of Python experience?')"
                  rows={2}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Press Enter to send, Shift+Enter for new line
                </p>
              </div>
              <button
                type="submit"
                disabled={!input.trim() || queryMutation.isPending}
                className="btn-primary px-6 py-3 h-fit"
              >
                <Send className="h-5 w-5" />
              </button>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  );
};

// Message Component
const Message = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start space-x-4 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-primary-600' : 'bg-primary-100'
        }`}>
          {isUser ? (
            <User className="h-5 w-5 text-white" />
          ) : (
            <Bot className="h-5 w-5 text-primary-600" />
          )}
        </div>
      </div>

      {/* Content */}
      <div className={`flex-1 ${isUser ? 'flex justify-end' : ''}`}>
        <div className={`max-w-3xl ${isUser ? 'text-right' : ''}`}>
          <div className={`rounded-lg p-4 ${
            isUser 
              ? 'bg-primary-600 text-white' 
              : 'bg-gray-100 text-gray-900'
          }`}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>

          {/* Sources */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="mt-3 space-y-2">
              <p className="text-xs text-gray-500 font-medium">Sources:</p>
              {message.sources.map((source, idx) => (
                <SourceCard key={idx} source={source} />
              ))}
            </div>
          )}

          {/* Timestamp */}
          <p className="mt-2 text-xs text-gray-400">
            {message.timestamp.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
};

// Source Card Component
const SourceCard = ({ source }) => (
  <div className="flex items-start space-x-3 p-3 bg-white border border-gray-200 rounded-lg">
    <FileText className="h-4 w-4 text-gray-400 flex-shrink-0 mt-0.5" />
    <div className="flex-1 min-w-0">
      <p className="text-sm font-medium text-gray-900">
        {source.candidate_name}
      </p>
      <p className="text-xs text-gray-500 line-clamp-2 mt-1">
        {source.excerpt}
      </p>
    </div>
    {source.relevance_score && (
      <div className="flex-shrink-0">
        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-primary-50 text-primary-700">
          {(source.relevance_score * 100).toFixed(0)}%
        </span>
      </div>
    )}
  </div>
);

// Empty State Component
const EmptyState = ({ onExampleClick }) => {
  const examples = [
    "Who has 5+ years of Python experience?",
    "Find candidates with AWS and Docker skills",
    "Show me senior engineers with machine learning background",
    "Who has worked at FAANG companies?",
    "Which candidates speak multiple languages?",
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-12">
      <div className="mb-8">
        <div className="mx-auto h-16 w-16 rounded-full bg-primary-100 flex items-center justify-center mb-4">
          <Sparkles className="h-8 w-8 text-primary-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Ask me anything about candidates
        </h3>
        <p className="text-sm text-gray-500 max-w-md">
          Use natural language to search and analyze resumes. I'll use AI to find the most relevant candidates.
        </p>
      </div>

      <div className="w-full max-w-2xl">
        <p className="text-xs text-gray-500 font-medium mb-3 text-left">
          Try these examples:
        </p>
        <div className="space-y-2">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => onExampleClick(example)}
              className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
            >
              <p className="text-sm text-gray-700">{example}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-8 max-w-md">
        <div className="flex items-start space-x-2 text-left">
          <div className="flex-shrink-0 mt-1">
            <div className="h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-xs text-blue-600">💡</span>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            <strong>Tip:</strong> The more specific your query, the better the results. 
            You can ask follow-up questions to refine your search.
          </p>
        </div>
      </div>
    </div>
  );
};
