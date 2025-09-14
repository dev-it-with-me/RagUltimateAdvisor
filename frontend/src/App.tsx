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

const SourceDocumentCard = ({ doc }: SourceDocumentCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

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
    <div className="rounded-lg border border-border bg-card hover:bg-muted/20 transition-colors duration-200">
      <div className="p-4">
        {/* Header with file info and score */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              <div className="flex flex-col">
                <span className="text-sm font-medium text-foreground">
                  {doc.metadata.file_name}
                </span>
                {doc.metadata.page && (
                  <span className="text-xs text-muted-foreground">
                    Page {doc.metadata.page}
                  </span>
                )}
              </div>
            </div>
            <Badge
              variant={getRelevanceBadgeVariant(doc.score)}
              className="text-xs"
            >
              {getRelevanceLabel(doc.score)}
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              className="h-6 px-2 text-xs hover:bg-primary/10"
            >
              <Download className="w-3 h-3 mr-1" />
              Download
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Similarity:</span>
            <div className="flex items-center gap-1">
              <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-300"
                  style={{
                    width: `${Math.min(doc.score * 100, 100)}%`,
                  }}
                ></div>
              </div>
              <span className="text-xs font-mono text-muted-foreground min-w-[3rem] text-right">
                {doc.score.toFixed(3)}
              </span>
            </div>
          </div>
        </div>

        {/* Content preview */}
        <div className="text-sm text-foreground leading-relaxed">
          <div className="relative">
            {doc.content.length > 200 ? (
              <>
                <p className="text-foreground/90">
                  {isExpanded
                    ? doc.content
                    : `${doc.content.substring(0, 200)}...`}
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="mt-2 h-6 px-2 text-xs text-primary hover:text-primary/80 hover:bg-primary/10"
                >
                  {isExpanded ? (
                    <>
                      <ChevronUp className="w-3 h-3 mr-1" />
                      Show less
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-3 h-3 mr-1" />
                      Show full content
                    </>
                  )}
                </Button>
              </>
            ) : (
              <p className="text-foreground/90">{doc.content}</p>
            )}
          </div>
        </div>
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

  const handleKeyPress = (e: React.KeyboardEvent) => {
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
    <div className="h-screen bg-background flex">
      {/* Sidebar */}
      <div className="w-80 bg-card border-r border-border flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-2 mb-4">
            <Bot className="w-6 h-6 text-primary" />
            <h1 className="text-xl font-semibold text-foreground">
              Ultimate Advisor
            </h1>
          </div>
          <Button className="w-full" size="sm" onClick={handleNewChat}>
            <Plus className="w-4 h-4 mr-2" />
            New Chat
          </Button>
        </div>

        {/* Chat History */}
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-2">
            {isLoadingHistory ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="ml-2 text-sm text-muted-foreground">
                  Loading chats...
                </span>
              </div>
            ) : historyError ? (
              <div className="flex items-center justify-center py-4 text-red-400">
                <AlertCircle className="w-4 h-4 mr-2" />
                <span className="text-sm">Failed to load chat history</span>
              </div>
            ) : chatList.length === 0 ? (
              <div className="text-center py-4">
                <p className="text-sm text-muted-foreground">No chats yet</p>
                <p className="text-xs text-muted-foreground">
                  Start a new conversation!
                </p>
              </div>
            ) : (
              chatList.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => handleSelectChat(chat.id)}
                  className={`w-full text-left p-3 rounded-lg flex items-center gap-3 transition-colors ${
                    activeChat === chat.id
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-muted text-muted-foreground"
                  }`}
                >
                  <div className="flex-1 min-w-0">
                    <span className="text-sm block truncate">{chat.name}</span>
                    <span
                      className={`text-xs ${
                        activeChat === chat.id
                          ? "text-black/60"
                          : "text-muted-foreground"
                      }`}
                    >
                      {new Date(chat.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {!chat.success && (
                    <AlertCircle className="w-3 h-3 text-red-400 flex-shrink-0" />
                  )}
                </button>
              ))
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Chat Messages Area */}
        <div className="flex-1 p-6">
          <ScrollArea className="h-full">
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Messages */}
              <div className="space-y-4">
                {isLoadingQuery && activeChat ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin" />
                    <span className="ml-2 text-muted-foreground">
                      Loading conversation...
                    </span>
                  </div>
                ) : currentMessages.length === 0 ? (
                  <div className="text-center py-8">
                    <Bot className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-medium text-foreground mb-2">
                      Welcome to Ultimate Advisor
                    </h3>
                    <p className="text-muted-foreground">
                      Ask me anything about Ultimate Frisbee rules and
                      strategies!
                    </p>
                  </div>
                ) : (
                  currentMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex gap-3 ${
                        message.type === "user" ? "flex-row-reverse" : ""
                      }`}
                    >
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-primary text-primary-foreground">
                          {message.type === "assistant" ? (
                            <Bot className="w-4 h-4" />
                          ) : (
                            <User className="w-4 h-4" />
                          )}
                        </AvatarFallback>
                      </Avatar>
                      <div
                        className={`max-w-[70%] ${
                          message.type === "user" ? "text-right" : ""
                        }`}
                      >
                        {message.type === "assistant" && (
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium text-foreground">
                              AI Ultimate Advisor
                            </span>
                          </div>
                        )}
                        {message.type === "user" && (
                          <div className="flex items-center justify-end gap-2 mb-1">
                            <span className="text-sm font-medium text-foreground">
                              You
                            </span>
                          </div>
                        )}
                        <div
                          className={`p-3 rounded-lg ${
                            message.type === "user"
                              ? "bg-primary text-primary-foreground"
                              : "bg-muted text-foreground"
                          }`}
                        >
                          <p className="text-sm whitespace-pre-wrap">
                            {message.content}
                          </p>
                        </div>
                        <div className="flex items-center justify-end mt-1">
                          <span className="text-xs text-muted-foreground">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))
                )}

                {/* Show sending indicator */}
                {isSendingMessage && (
                  <div className="flex gap-3">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-primary text-primary-foreground">
                        <Bot className="w-4 h-4" />
                      </AvatarFallback>
                    </Avatar>
                    <div className="max-w-[70%]">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-foreground">
                          AI Ultimate Advisor
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-muted text-foreground">
                        <div className="flex items-center gap-2">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span className="text-sm">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Source Documents Section */}
              <div className="mt-8">
                <h2 className="text-lg font-semibold text-foreground mb-4">
                  Source Documents
                </h2>
                {currentSourceDocuments.length === 0 ? (
                  <div className="rounded-lg border border-border p-8 text-center">
                    <p className="text-muted-foreground">
                      {currentMessages.length === 0
                        ? "Source documents will appear here when you ask a question"
                        : "No source documents found for this query"}
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {currentSourceDocuments.map((doc, index) => (
                      <SourceDocumentCard key={index} doc={doc} index={index} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>
        </div>

        {/* Message Input Area */}
        <div className="border-t border-border p-6">
          <div className="max-w-4xl mx-auto">
            {/* Error display */}
            {sendError && (
              <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                <div className="flex items-center gap-2 text-red-400">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    Error sending message
                  </span>
                </div>
                <p className="text-sm text-red-300 mt-1">{sendError}</p>
              </div>
            )}

            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Input
                  placeholder="Ask about Ultimate Frisbee rules..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="pr-12"
                  disabled={isSendingMessage}
                />
              </div>
              <Button
                onClick={handleSendMessage}
                className="px-4"
                disabled={!inputMessage.trim() || isSendingMessage}
              >
                {isSendingMessage ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
