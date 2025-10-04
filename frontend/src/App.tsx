import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Plus,
  Bot,
  User,
  Send,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Download,
  FileText,
  Sparkles,
  History,
  Lightbulb,
  BookOpen,
} from "lucide-react";
import {
  useQueryHistory,
  useQuery,
  useQueryRAG,
  convertQueryResponseToMessages,
  convertQueryHistoryToChats,
} from "@/hooks/useApi";
import type { Message, SourceDocument } from "@/types/api";

// Source Document Card Component
interface SourceDocumentCardProps {
  doc: SourceDocument;
  index: number;
}

const SourceDocumentCard = ({ doc, index }: SourceDocumentCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const docPosition = index + 1;

  const handleDownload = () => {
    const downloadUrl = `/files/download/${encodeURIComponent(
      doc.metadata.file_name
    )}`;
    window.open(downloadUrl, "_blank");
  };

  const getRelevanceBadgeVariant = (score: number) => {
    if (score >= 0.7) return "default";
    if (score >= 0.5) return "secondary";
    return "outline";
  };

  const getRelevanceLabel = (score: number) => {
    if (score >= 0.7) return "High Relevance";
    if (score >= 0.5) return "Medium Relevance";
    return "Low Relevance";
  };

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border/60 bg-card/70 px-6 py-5 backdrop-blur transition-all duration-300 hover:border-primary/60 hover:bg-card/80">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="flex flex-wrap items-start justify-between gap-4 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/15 text-xs font-semibold text-primary">
            #{docPosition}
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-foreground">
              <FileText className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold leading-tight">
                {doc.metadata.file_name}
              </span>
            </div>
            {doc.metadata.page && (
              <span className="text-xs text-muted-foreground">
                Page {doc.metadata.page}
              </span>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <Badge
              variant={getRelevanceBadgeVariant(doc.score)}
              className="text-[11px] uppercase tracking-wide"
            >
              {getRelevanceLabel(doc.score)}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              className="h-7 px-2 text-[11px] hover:bg-primary/10"
            >
              <Download className="mr-1 h-3 w-3" />
              Save PDF
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <span>Similarity</span>
            <div className="flex items-center gap-2">
              <div className="relative h-1.5 w-16 overflow-hidden rounded-full bg-muted/60">
                <div
                  className="absolute inset-y-0 left-0 rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${Math.min(doc.score * 100, 100)}%` }}
                />
              </div>
              <span className="font-mono text-[11px] text-primary/80">
                {doc.score.toFixed(3)}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="relative text-sm leading-relaxed text-foreground/90">
        {doc.content.length > 200 ? (
          <>
            <p className="transition-all duration-300">
              {isExpanded ? doc.content : `${doc.content.substring(0, 200)}...`}
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="mt-3 h-7 px-2 text-[11px] text-primary hover:text-primary/80 hover:bg-primary/10"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="mr-1 h-3 w-3" />
                  Show less
                </>
              ) : (
                <>
                  <ChevronDown className="mr-1 h-3 w-3" />
                  Read more
                </>
              )}
            </Button>
          </>
        ) : (
          <p>{doc.content}</p>
        )}
      </div>
    </div>
  );
};

function App() {
  const [inputMessage, setInputMessage] = useState("");
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [currentMessages, setCurrentMessages] = useState<Message[]>([]);
  const [currentSourceDocuments, setCurrentSourceDocuments] = useState<
    SourceDocument[]
  >([]);

  // API hooks
  const {
    queryHistory,
    isLoading: isLoadingHistory,
    isError: historyError,
    mutate: refreshHistory,
  } = useQueryHistory(20, 0);
  const { query: selectedQuery, isLoading: isLoadingQuery } =
    useQuery(activeChat);
  const {
    sendQuery,
    isLoading: isSendingMessage,
    error: sendError,
  } = useQueryRAG();

  // Convert query history to chat list
  const chatList = queryHistory ? convertQueryHistoryToChats(queryHistory) : [];
  const activeChatMeta = activeChat
    ? chatList.find((chat) => chat.id === activeChat)
    : null;

  const suggestionPills = [
    "When is play considered dead?",
    "How do marking infractions reset the stall?",
    "What counts as a strip foul?",
  ];

  const showWelcomeState =
    currentMessages.length === 0 && !isSendingMessage && !isLoadingQuery;

  const showHistoryEmptyState =
    chatList.length === 0 && !isLoadingHistory && !historyError;

  const formatTimestamp = (timestamp: string) =>
    new Date(timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  // Update messages when a chat is selected
  useEffect(() => {
    if (selectedQuery) {
      const messages: Message[] = [
        {
          id: `${selectedQuery.query_history.id}-user`,
          type: "user",
          content: selectedQuery.query_history.query,
          timestamp: selectedQuery.query_history.created_at,
        },
        {
          id: `${selectedQuery.query_history.id}-assistant`,
          type: "assistant",
          content: selectedQuery.query_history.chat_response,
          timestamp: selectedQuery.query_history.created_at,
          source_documents: selectedQuery.source_documents.map((doc) => ({
            content: doc.content_preview,
            score: doc.similarity_score,
            metadata: doc.document_metadata || {
              file_name: "Unknown",
              page: undefined,
              source: undefined,
            },
          })),
        },
      ];
      setCurrentMessages(messages);

      // Set source documents for the table
      const sourceDocs: SourceDocument[] = selectedQuery.source_documents.map(
        (doc) => ({
          content: doc.content_preview,
          score: doc.similarity_score,
          metadata: doc.document_metadata || {
            file_name: "Unknown",
            page: undefined,
            source: undefined,
          },
        })
      );
      setCurrentSourceDocuments(sourceDocs);
    } else {
      setCurrentMessages([]);
      setCurrentSourceDocuments([]);
    }
  }, [selectedQuery]);

  const handleSuggestionClick = (value: string) => {
    setInputMessage(value);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isSendingMessage) return;

    const queryText = inputMessage.trim();
    setInputMessage("");

    try {
      // Add user message immediately for better UX
      const tempUserMessage: Message = {
        id: `temp-${Date.now()}-user`,
        type: "user",
        content: queryText,
        timestamp: new Date().toISOString(),
      };

      setCurrentMessages((prev) => [...prev, tempUserMessage]);
      setActiveChat(null); // Clear active chat since we're creating a new conversation

      // Send query to API
      const response = await sendQuery({ query: queryText, top_k: 2 });

      if (response) {
        // Replace temp message with real messages
        const newMessages = convertQueryResponseToMessages(
          queryText,
          response,
          `query-${Date.now()}`
        );
        setCurrentMessages(newMessages);
        setCurrentSourceDocuments(response.source_documents);

        // Refresh history to show the new query
        refreshHistory();
      } else {
        // Remove temp message if there was an error
        setCurrentMessages((prev) =>
          prev.filter((msg) => msg.id !== tempUserMessage.id)
        );
      }
    } catch (error) {
      console.error("Error sending message:", error);
      // Remove temp message on error
      setCurrentMessages((prev) =>
        prev.filter((msg) => msg.id.startsWith("temp-"))
      );
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = () => {
    setActiveChat(null);
    setCurrentMessages([]);
    setCurrentSourceDocuments([]);
  };

  const handleSelectChat = (chatId: string) => {
    setActiveChat(chatId);
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0">
        <div className="absolute -left-24 -top-32 h-72 w-72 rounded-full bg-accent/35 blur-3xl opacity-60" />
        <div className="absolute right-[-6rem] top-1/3 h-80 w-80 rounded-full bg-primary/30 blur-3xl opacity-60" />
        <div className="absolute bottom-[-5rem] left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-secondary/30 blur-3xl opacity-60" />
      </div>

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-[1600px] flex-col gap-6 px-4 py-6 lg:flex-row lg:px-12 lg:py-10">
        {/* Main Content */}
        <main className="order-1 flex-1 overflow-hidden rounded-3xl border border-border/60 bg-card/60 shadow-[0_25px_65px_-45px_rgba(0,0,0,0.85)] backdrop-blur">
          <div className="flex h-full flex-col">
            <div className="border-b border-border/50 bg-card/70 px-6 py-6 md:px-10 md:py-8">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="space-y-3">
                  <span className="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-primary">
                    <Sparkles className="h-3.5 w-3.5" />
                    Conversation
                  </span>
                  <div>
                    <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
                      {activeChatMeta
                        ? activeChatMeta.name
                        : "Start a new chat"}
                    </h2>
                    <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                      {activeChatMeta
                        ? "Review your selected discussion or continue exploring Ultimate Frisbee rulings."
                        : "Ask a question about WFDF rules, strategy nuances, or tricky in-game situations."}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {activeChatMeta && (
                    <Badge className="rounded-full bg-primary/20 text-[11px] font-normal text-primary">
                      Saved{" "}
                      {new Date(activeChatMeta.created_at).toLocaleDateString()}
                    </Badge>
                  )}
                </div>
              </div>
              {showWelcomeState && (
                <div className="mt-8 rounded-3xl border border-border/50 bg-background/50 p-8 text-center backdrop-blur md:p-10">
                  <div className="mx-auto max-w-2xl space-y-6">
                    <div className="inline-flex items-center gap-2 rounded-full border border-accent/40 bg-accent/15 px-4 py-1 text-[11px] font-semibold uppercase tracking-wide text-accent-foreground/90">
                      <Bot className="h-4 w-4 text-accent-foreground/90" />
                      Welcome aboard
                    </div>
                    <div className="space-y-3">
                      <h3 className="text-2xl font-semibold md:text-3xl">
                        Your Ultimate Frisbee rulebook, in chat form
                      </h3>
                      <p className="text-sm text-muted-foreground md:text-base">
                        Use conversational questions to explore scenarios,
                        confirm rulings, or pull citations from the official
                        WFDF rule set.
                      </p>
                    </div>
                    <div className="flex flex-wrap justify-center gap-3">
                      {suggestionPills.map((suggestion) => (
                        <Button
                          key={suggestion}
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="rounded-full border-border/60 bg-background/70 text-xs text-muted-foreground transition hover:border-primary/50 hover:bg-primary/10 hover:text-foreground"
                        >
                          {suggestion}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex-1 overflow-hidden">
              <ScrollArea className="h-full px-6 py-6 md:px-10 md:py-8">
                <div className="mx-auto flex max-w-4xl flex-col gap-8">
                  <div className="flex flex-col gap-6">
                    {isLoadingQuery && activeChat ? (
                      <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-border/60 bg-background/50 p-10 text-center text-sm text-muted-foreground">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                        Loading conversation...
                      </div>
                    ) : currentMessages.length === 0 ? (
                      !showWelcomeState && (
                        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-border/60 bg-background/50 p-10 text-center text-sm text-muted-foreground">
                          <Bot className="h-10 w-10 text-muted-foreground" />
                          Ask a question to see the conversation flow here.
                        </div>
                      )
                    ) : (
                      currentMessages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex items-end gap-3 ${
                            message.type === "user" ? "flex-row-reverse" : ""
                          }`}
                        >
                          <Avatar className="h-9 w-9 border border-border/60 bg-background/80 text-primary">
                            <AvatarFallback>
                              {message.type === "assistant" ? (
                                <Bot className="h-4 w-4" />
                              ) : (
                                <User className="h-4 w-4" />
                              )}
                            </AvatarFallback>
                          </Avatar>
                          <div
                            className={`flex max-w-[78%] flex-col gap-2 ${
                              message.type === "user"
                                ? "items-end text-right"
                                : ""
                            }`}
                          >
                            <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground/80">
                              {message.type === "assistant"
                                ? "AI Ultimate Advisor"
                                : "You"}
                            </div>
                            <div
                              className={`rounded-2xl border px-4 py-3 text-sm leading-relaxed shadow-sm transition ${
                                message.type === "user"
                                  ? "border-primary/70 bg-primary text-primary-foreground shadow-primary/20"
                                  : "border-border/60 bg-background/65 backdrop-blur"
                              }`}
                            >
                              <p className="whitespace-pre-wrap text-sm md:text-[15px]">
                                {message.content}
                              </p>
                            </div>
                            <span className="text-[11px] text-muted-foreground/80">
                              {formatTimestamp(message.timestamp)}
                            </span>
                          </div>
                        </div>
                      ))
                    )}

                    {isSendingMessage && (
                      <div className="flex items-end gap-3">
                        <Avatar className="h-9 w-9 border border-border/60 bg-background/80 text-primary">
                          <AvatarFallback>
                            <Bot className="h-4 w-4" />
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex max-w-[78%] flex-col gap-2">
                          <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground/80">
                            AI Ultimate Advisor
                          </div>
                          <div className="rounded-2xl border border-border/60 bg-background/65 px-4 py-3 backdrop-blur">
                            <div className="flex items-center gap-2 text-sm">
                              <Loader2 className="h-4 w-4 animate-spin text-primary" />
                              Thinking...
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
                      <BookOpen className="h-5 w-5 text-primary" />
                      Source documents
                    </div>
                    {currentSourceDocuments.length === 0 ? (
                      <div className="rounded-2xl border border-dashed border-border/70 bg-background/40 p-8 text-center text-sm text-muted-foreground">
                        {currentMessages.length === 0
                          ? "Source documents will appear here once you ask something."
                          : "No supporting documents were returned for this response."}
                      </div>
                    ) : (
                      <div className="grid gap-4 lg:grid-cols-2">
                        {currentSourceDocuments.map((doc, index) => (
                          <SourceDocumentCard
                            key={index}
                            doc={doc}
                            index={index}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </ScrollArea>
            </div>

            <div className="border-t border-border/60 bg-card/70 px-6 py-6 md:px-10">
              <div className="mx-auto flex max-w-4xl flex-col gap-4">
                {sendError && (
                  <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
                    <div className="flex items-center gap-2 font-medium">
                      <AlertCircle className="h-4 w-4" />
                      Error sending message
                    </div>
                    <p className="mt-1 text-xs opacity-80">{sendError}</p>
                  </div>
                )}
                <div className="flex flex-col gap-3 sm:flex-row">
                  <div className="relative flex-1">
                    <Input
                      placeholder="Ask about Ultimate Frisbee rules..."
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      onKeyDown={handleKeyDown}
                      className="h-12 rounded-2xl border-border/60 bg-background/70 pr-16 text-sm shadow-inner shadow-black/30 backdrop-blur"
                      disabled={isSendingMessage}
                    />
                    <div className="pointer-events-none absolute inset-y-0 right-4 hidden items-center gap-2 text-[11px] text-muted-foreground sm:flex">
                      <span>Press</span>
                      <kbd className="rounded-md border border-border/60 bg-background/70 px-2 py-1 text-[10px] uppercase">
                        Enter
                      </kbd>
                    </div>
                  </div>
                  <Button
                    onClick={handleSendMessage}
                    className="h-12 rounded-2xl bg-primary/90 px-6 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/30 transition hover:bg-primary"
                    disabled={!inputMessage.trim() || isSendingMessage}
                  >
                    {isSendingMessage ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        Send
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Sidebar */}
        <aside className="order-2 flex w-full flex-col gap-6 rounded-3xl border border-border/60 bg-card/60 p-6 shadow-[0_20px_55px_-45px_rgba(0,0,0,0.8)] backdrop-blur lg:order-none lg:w-[320px]">
          <div className="space-y-5">
            <div className="space-y-3">
              <h1 className="text-2xl font-semibold leading-tight">
                Ultimate Advisor
              </h1>
              <p className="text-sm text-muted-foreground">
                Quickly clarify WFDF rulings, marking mechanics, and on-field
                scenarios.
              </p>
            </div>
            <Button
              className="h-11 w-full rounded-2xl bg-primary/90 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/30 transition hover:bg-primary"
              onClick={handleNewChat}
            >
              <Plus className="mr-2 h-4 w-4" />
              Start new conversation
            </Button>
          </div>

          <div className="rounded-2xl border border-border/50 bg-background/45 p-5 backdrop-blur-md">
            <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <Lightbulb className="h-4 w-4 text-primary" />
              Try asking about
            </div>
            <ul className="mt-3 space-y-2 text-xs text-muted-foreground">
              {suggestionPills.map((suggestion) => (
                <li key={`tip-${suggestion}`}>
                  <button
                    type="button"
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="flex w-full items-center gap-2 rounded-xl border border-transparent bg-transparent px-2 py-1 text-left transition hover:border-primary/40 hover:bg-primary/10 hover:text-foreground"
                  >
                    <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-primary/60" />
                    {suggestion}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex-1 overflow-hidden">
            <div className="mb-3 flex items-center justify-between text-sm font-semibold text-muted-foreground">
              <div className="flex items-center gap-2 text-foreground">
                <History className="h-4 w-4 text-primary" />
                Conversations
              </div>
              <span className="text-[11px] uppercase tracking-wide text-muted-foreground/80">
                {chatList.length} saved
              </span>
            </div>
            <ScrollArea className="h-full pr-1">
              <div className="space-y-2">
                {isLoadingHistory ? (
                  <div className="flex items-center justify-center rounded-2xl border border-border/50 bg-background/45 p-6 text-sm text-muted-foreground">
                    <Loader2 className="mr-2 h-4 w-4 animate-spin text-primary" />
                    Loading chats...
                  </div>
                ) : historyError ? (
                  <div className="flex items-center justify-center rounded-2xl border border-red-500/40 bg-red-500/10 p-6 text-sm text-red-200">
                    <AlertCircle className="mr-2 h-4 w-4" />
                    Failed to load chat history
                  </div>
                ) : showHistoryEmptyState ? (
                  <div className="rounded-2xl border border-dashed border-border/60 bg-background/40 p-6 text-center text-sm text-muted-foreground">
                    No chats yet — start a conversation!
                  </div>
                ) : (
                  chatList.map((chat) => (
                    <button
                      key={chat.id}
                      onClick={() => handleSelectChat(chat.id)}
                      className={`w-full rounded-2xl border px-4 py-4 text-left transition-all ${
                        activeChat === chat.id
                          ? "border-primary/60 bg-primary/15 text-foreground shadow-[0_12px_30px_-22px_rgba(0,0,0,0.8)]"
                          : "border-transparent bg-background/45 text-muted-foreground hover:border-primary/40 hover:bg-primary/10 hover:text-foreground"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold leading-tight">
                            {chat.name}
                          </p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {new Date(chat.created_at).toLocaleDateString()} •{" "}
                            {new Date(chat.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </p>
                        </div>
                        {!chat.success && (
                          <Badge
                            variant="outline"
                            className="rounded-full border-red-400/60 bg-transparent text-[11px] text-red-300"
                          >
                            Needs review
                          </Badge>
                        )}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default App;
