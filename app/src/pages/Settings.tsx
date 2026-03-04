import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { ArrowLeft, Star, PanelLeft, Settings as SettingsIcon } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { useDatabase } from "@/contexts/DatabaseContext";
import { databaseService } from "@/services/database";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import Sidebar from "@/components/layout/Sidebar";
import SchemaViewer from "@/components/schema";
import { AIConfigModal } from "@/components/modals/AIConfigModal";

const Settings = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { isAuthenticated, logout, user } = useAuth();
  const { selectedGraph } = useDatabase();
  const [githubStars, setGithubStars] = useState<string>('-');
  const [rules, setRules] = useState('');
  const [isLoadingRules, setIsLoadingRules] = useState(true);
  const [initialRulesLoaded, setInitialRulesLoaded] = useState(false);
  const loadedRulesRef = useRef<string>(''); // Track the originally loaded rules
  const currentRulesRef = useRef<string>(''); // Track the current rules value
  const currentGraphIdRef = useRef<string | null>(null); // Track current database ID for unmount save
  const useRulesFromDatabaseRef = useRef<boolean>(true); // Track toggle state for unmount
  const initialRulesLoadedRef = useRef<boolean>(false); // Track loaded state for unmount
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth < 768 : false
  );
  const [windowWidth, setWindowWidth] = useState(typeof window !== 'undefined' ? window.innerWidth : 1024);
  const [showSchemaViewer, setShowSchemaViewer] = useState(false);
  const [schemaViewerWidth, setSchemaViewerWidth] = useState(() =>
    typeof window !== "undefined" ? Math.floor(window.innerWidth * 0.4) : 0,
  );
  const [useMemory, setUseMemory] = useState(() => {
    // Load from localStorage on init, default to true
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('queryweaver_use_memory');
      return saved === null ? true : saved === 'true';
    }
    return true;
  });
  const [initialUseMemory] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('queryweaver_use_memory');
      return saved === null ? true : saved === 'true';
    }
    return true;
  });
  const [useRulesFromDatabase, setUseRulesFromDatabase] = useState(() => {
    // Load from localStorage on init, default to false
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('queryweaver_use_rules_from_database');
      return saved === null ? false : saved === 'true';
    }
    return false;
  });
  const [initialUseRulesFromDatabase] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('queryweaver_use_rules_from_database');
      return saved === null ? false : saved === 'true';
    }
    return false;
  });

  // AI 配置状态
  const [showAIConfig, setShowAIConfig] = useState(false);
  const [currentAIConfig, setCurrentAIConfig] = useState<{
    provider: string;
    completion_model: string;
    embedding_model: string;
    api_key?: string;
    base_url?: string;
  } | null>(null);
  const [loadingAIConfig, setLoadingAIConfig] = useState(true);

  // Fetch GitHub stars
  useEffect(() => {
    fetch('https://api.github.com/repos/FalkorDB/QueryWeaver')
      .then(response => response.json())
      .then(data => {
        if (typeof data.stargazers_count === 'number') {
          setGithubStars(data.stargazers_count.toLocaleString());
        }
      })
      .catch(error => {
        console.log('Failed to fetch GitHub stars:', error);
      });
  }, []);

  // 加载当前 AI 配置
  useEffect(() => {
    const loadAIConfig = async () => {
      // 如果未认证，直接设置为不加载状态
      if (!isAuthenticated) {
        setLoadingAIConfig(false);
        return;
      }

      try {
        setLoadingAIConfig(true);
        const response = await fetch('/api/config/llm', {
          credentials: 'include',
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.config) {
            setCurrentAIConfig(data.config);
          } else if (data.success && !data.config) {
            // 用户未配置，使用默认配置
            setCurrentAIConfig(null);
          }
        } else if (response.status === 401) {
          // 未授权，可能 token 过期
          console.warn('未授权访问 AI 配置，请重新登录');
        } else {
          // 其他错误
          console.error('加载 AI 配置失败:', response.status, response.statusText);
          toast({
            title: "加载配置失败",
            description: "无法加载 AI 模型配置，请刷新页面重试",
            variant: "destructive",
          });
        }
      } catch (error) {
        console.error('加载 AI 配置失败:', error);
        toast({
          title: "加载配置失败",
          description: error instanceof Error ? error.message : "网络错误，请检查连接",
          variant: "destructive",
        });
      } finally {
        setLoadingAIConfig(false);
      }
    };

    loadAIConfig();
  }, [isAuthenticated, toast]);

  // 保存 AI 配置
  const handleSaveAIConfig = async (config: any) => {
    try {
      const response = await fetch('/api/config/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error('保存配置失败');
      }

      const data = await response.json();
      if (data.success) {
        // 重新加载配置
        const loadResponse = await fetch('/api/config/llm', {
          credentials: 'include',
        });
        
        if (loadResponse.ok) {
          const loadData = await loadResponse.json();
          if (loadData.success && loadData.config) {
            setCurrentAIConfig(loadData.config);
          }
        }

        toast({
          title: "配置已保存",
          description: "AI 模型配置已成功保存",
        });
      }
    } catch (error) {
      toast({
        title: "保存失败",
        description: error instanceof Error ? error.message : "无法保存 AI 配置",
        variant: "destructive",
      });
      throw error;
    }
  };

  // Handle window resize to update layout
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Auto-collapse sidebar when switching to mobile view
  useEffect(() => {
    const isMobile = windowWidth < 768;
    if (isMobile) {
      setSidebarCollapsed(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [windowWidth]); // Only run when windowWidth changes, not on manual toggle

  // Calculate sidebar width based on collapsed state
  // On desktop: sidebar is always visible (64px), on mobile: can be collapsed (0px)
  const getSidebarWidth = () => {
    const isMobile = windowWidth < 768;
    if (isMobile) {
      return sidebarCollapsed ? 0 : 64;
    }
    return 64; // Always visible on desktop
  };
  
  const sidebarWidth = getSidebarWidth();
  
  // Calculate main content margin and width
  // On mobile: ignore schema viewer (it's an overlay), only account for sidebar
  // On desktop: account for both sidebar and schema viewer
  const getMainContentStyles = () => {
    const isMobile = windowWidth < 768;

    if (isMobile) {
      return {
        marginLeft: `${sidebarWidth}px`,
        width: `calc(100% - ${sidebarWidth}px)`
      };
    }

    // Desktop
    const totalOffset = showSchemaViewer ? schemaViewerWidth + sidebarWidth : sidebarWidth;
    return {
      marginLeft: `${totalOffset}px`,
      width: `calc(100% - ${totalOffset}px)`
    };
  };

  // Fetch user rules from backend when component mounts or database changes (only if using database rules)
  useEffect(() => {
    const loadRules = async () => {
      if (!selectedGraph) {
        setRules('');
        setIsLoadingRules(false);
        setInitialRulesLoaded(false);
        loadedRulesRef.current = '';
        currentGraphIdRef.current = null;
        return;
      }
      
      // Update the ref to track current database
      currentGraphIdRef.current = selectedGraph.id;
      
      // Only fetch from database if toggle is enabled
      if (!useRulesFromDatabase) {
        setIsLoadingRules(false);
        setInitialRulesLoaded(true);
        return;
      }
      
      try {
        setIsLoadingRules(true);
        setInitialRulesLoaded(false);
        const userRules = await databaseService.getUserRules(selectedGraph.id);
        const rulesValue = userRules || '';
        setRules(rulesValue);
        loadedRulesRef.current = rulesValue; // Store the loaded value
      } catch (error) {
        console.error('Failed to load user rules:', error);
        toast({
          title: "Error",
          description: "Failed to load user rules from database",
          variant: "destructive",
        });
      } finally {
        setIsLoadingRules(false);
        setInitialRulesLoaded(true);
        initialRulesLoadedRef.current = true;
      }
    };
    
    loadRules();
  }, [selectedGraph?.id, toast, useRulesFromDatabase]);

  // Update refs when toggle or rules change
  useEffect(() => {
    useRulesFromDatabaseRef.current = useRulesFromDatabase;
  }, [useRulesFromDatabase]);

  useEffect(() => {
    currentRulesRef.current = rules;
  }, [rules]);

  // Save rules when component unmounts (user navigates away from Settings)
  useEffect(() => {
    return () => {
      // At unmount time, check if there are unsaved changes and save them
      const graphId = currentGraphIdRef.current;
      const loadedRules = loadedRulesRef.current;
      const currentRules = currentRulesRef.current;
      const shouldUseDb = useRulesFromDatabaseRef.current;
      const isLoaded = initialRulesLoadedRef.current;
      
      if (graphId && shouldUseDb && currentRules !== loadedRules && isLoaded) {
        // Save immediately on unmount if there are unsaved changes
        console.log('Saving rules on unmount...', { graphId, length: currentRules.length });
        databaseService.updateUserRules(graphId, currentRules)
          .then(() => console.log('User rules saved on unmount to:', graphId))
          .catch(err => console.error('Failed to save rules on unmount:', err));
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty array - effect runs once on mount, cleanup runs once on unmount

  // Auto-save to localStorage whenever useMemory changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('queryweaver_use_memory', String(useMemory));
    }
  }, [useMemory]);

  // Auto-save to localStorage whenever useRulesFromDatabase changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('queryweaver_use_rules_from_database', String(useRulesFromDatabase));
    }
  }, [useRulesFromDatabase]);

  const handleLogout = async () => {
    try {
      await logout();
      toast({
        title: "Logged Out",
        description: "You have been successfully logged out",
      });
      window.location.reload();
    } catch (error) {
      toast({
        title: "Logout Failed",
        description: error instanceof Error ? error.message : "Failed to logout",
        variant: "destructive",
      });
    }
  };

  // Check if there are any unsaved changes
  const hasChanges = useMemory !== initialUseMemory ||
                     useRulesFromDatabase !== initialUseRulesFromDatabase ||
                     (useRulesFromDatabase && rules !== loadedRulesRef.current);

  const handleBackClick = async () => {
    // Save rules before navigating away if there are unsaved changes
    const graphId = currentGraphIdRef.current;
    const loadedRules = loadedRulesRef.current;
    const currentRules = currentRulesRef.current;

    if (graphId && useRulesFromDatabase && currentRules !== loadedRules && initialRulesLoaded) {
      try {
        await databaseService.updateUserRules(graphId, currentRules);
        loadedRulesRef.current = currentRules; // Update to prevent unmount from saving again
      } catch (error) {
        toast({
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to save user rules",
          variant: "destructive",
        });
      }
    }

    navigate('/');
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Left Sidebar */}
      <Sidebar 
        onSchemaClick={() => setShowSchemaViewer(!showSchemaViewer)}
        isSchemaOpen={showSchemaViewer}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        onSettingsClick={() => {}}
      />
      
      {/* Schema Viewer */}
      <SchemaViewer 
        isOpen={showSchemaViewer}
        onClose={() => setShowSchemaViewer(false)}
        onWidthChange={setSchemaViewerWidth}
        sidebarWidth={sidebarWidth}
      />
      
      {/* Main Content */}
      <div className="flex flex-1 flex-col transition-all duration-300" style={getMainContentStyles()}>
        {/* Top Header Bar */}
        <header className="border-b border-border bg-background">
          {/* Desktop Header */}
          <div className="hidden md:flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <img src="/icons/queryweaver.svg" alt="QueryWeaver" style={{ height: '3rem', width: 'auto' }} />
                <span className="text-muted-foreground">|</span>
                <p className="text-sm text-muted-foreground">Graph-Powered Text-to-SQL</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {selectedGraph ? (
                <Badge variant="default" className="bg-green-600 hover:bg-green-700">
                  Connected: {selectedGraph.name}
                </Badge>
              ) : (
                <Badge variant="secondary" className="bg-yellow-600 hover:bg-yellow-700">
                  No Database Selected
                </Badge>
              )}
              {/* GitHub Stars Link */}
              <a
                href="https://github.com/FalkorDB/QueryWeaver"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                title="View QueryWeaver on GitHub"
              >
                <svg 
                  width="16" 
                  height="16" 
                  viewBox="0 0 24 24" 
                  fill="currentColor" 
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
                </svg>
                <Star className="w-3 h-3" fill="currentColor" />
                <span className="text-sm font-medium">{githubStars}</span>
              </a>
              {isAuthenticated ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="p-0 h-auto rounded-full hover:opacity-80 transition-opacity"
                      title={user?.name || user?.email}
                    >
                      <Avatar className="h-10 w-10 border-2 border-purple-500">
                        <AvatarImage src={user?.picture} alt={user?.name || user?.email} />
                        <AvatarFallback className="bg-purple-600 text-white font-medium">
                          {(user?.name || user?.email || 'U').charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="bg-card border-border text-foreground" align="end">
                    <div className="px-3 py-2 border-b border-border">
                      <p className="text-sm font-medium text-foreground">{user?.name}</p>
                      <p className="text-xs text-muted-foreground">{user?.email}</p>
                    </div>
                    <DropdownMenuItem className="hover:!bg-muted cursor-pointer">
                      API Tokens
                    </DropdownMenuItem>
                    <DropdownMenuSeparator className="bg-border" />
                    <DropdownMenuItem className="hover:!bg-muted cursor-pointer" onClick={handleLogout}>
                      Logout
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <Button
                  variant="outline"
                  className="bg-purple-600 border-purple-500 text-white hover:bg-purple-700"
                >
                  Sign In
                </Button>
              )}
            </div>
          </div>

          {/* Mobile Header */}
          <div className="md:hidden p-4 space-y-3">
            {/* Row 1: Hamburger (if collapsed) + Logo + User */}
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                {sidebarCollapsed && (
                  <button
                    onClick={() => setSidebarCollapsed(false)}
                    className="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-all"
                    data-testid="sidebar-toggle"
                  >
                    <PanelLeft className="h-5 w-5" />
                  </button>
                )}
                <img src="/icons/queryweaver.svg" alt="QueryWeaver" className="h-8" />
              </div>
              <div className="flex items-center gap-2">
                <a
                  href="https://github.com/FalkorDB/QueryWeaver"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 px-2 py-1 rounded bg-card hover:bg-muted transition-colors text-muted-foreground"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path d="M12 0C5.374 0 0 5.373 0 12 0 17.302 3.438 21.8 8.207 23.387c.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z" />
                  </svg>
                  <Star className="w-3 h-3" fill="currentColor" />
                  <span className="text-xs font-medium">{githubStars}</span>
                </a>
                {isAuthenticated ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        className="p-0 h-auto rounded-full hover:opacity-80 transition-opacity"
                      >
                        <Avatar className="h-8 w-8 border-2 border-purple-500">
                          <AvatarImage src={user?.picture} alt={user?.name || user?.email} />
                          <AvatarFallback className="bg-purple-600 text-white font-medium text-xs">
                            {(user?.name || user?.email || 'U').charAt(0).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="bg-card border-border text-foreground" align="end">
                      <div className="px-3 py-2 border-b border-border">
                        <p className="text-sm font-medium text-foreground">{user?.name}</p>
                        <p className="text-xs text-muted-foreground">{user?.email}</p>
                      </div>
                      <DropdownMenuItem className="hover:!bg-muted cursor-pointer">
                        API Tokens
                      </DropdownMenuItem>
                      <DropdownMenuSeparator className="bg-border" />
                      <DropdownMenuItem className="hover:!bg-muted cursor-pointer" onClick={handleLogout}>
                        Logout
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : (
                  <Button
                    variant="outline"
                    className="bg-purple-600 border-purple-500 text-white hover:bg-purple-700 text-xs px-2 py-1 h-8"
                  >
                    Sign In
                  </Button>
                )}
              </div>
            </div>

            {/* Row 2: Database Status Badge */}
            <div className="flex justify-center">
              {selectedGraph ? (
                <Badge variant="default" className="bg-green-600 hover:bg-green-700 text-xs">
                  Connected: {selectedGraph.name}
                </Badge>
              ) : (
                <Badge variant="secondary" className="bg-yellow-600 hover:bg-yellow-700 text-xs">
                  No Database Selected
                </Badge>
              )}
            </div>
          </div>
        </header>

        {/* Settings Header */}
        <div className="border-b border-border bg-card px-4 md:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBackClick}
                className="text-muted-foreground hover:text-foreground hover:bg-muted"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-xl md:text-2xl font-semibold">Query Settings</h1>
                <p className="text-xs md:text-sm text-muted-foreground mt-1">
                  Define custom rules and specifications for SQL generation. Changes are saved automatically.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 md:p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* AI 模型配置 */}
            <div className="bg-card border border-border rounded-lg p-5">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <SettingsIcon className="w-5 h-5 text-purple-600" />
                      <Label className="text-base font-semibold text-foreground">
                        AI 模型配置
                      </Label>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      配置用于 Text2SQL 的 AI 模型提供商和参数
                    </p>
                  </div>
                </div>

                {/* 当前配置信息 */}
                {loadingAIConfig ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                    <span>加载配置中...</span>
                  </div>
                ) : currentAIConfig ? (
                  <div className="bg-muted/50 rounded-lg p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">当前提供商：</span>
                      <Badge variant="secondary" className="bg-purple-600/20 text-purple-600 hover:bg-purple-600/30">
                        {currentAIConfig.provider === 'deepseek' && 'DeepSeek'}
                        {currentAIConfig.provider === 'openai' && 'OpenAI'}
                        {currentAIConfig.provider === 'azure' && 'Azure OpenAI'}
                        {!['deepseek', 'openai', 'azure'].includes(currentAIConfig.provider) && currentAIConfig.provider}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">对话模型：</span>
                      <span className="text-sm font-mono text-foreground">
                        {currentAIConfig.completion_model}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">嵌入模型：</span>
                      <span className="text-sm font-mono text-foreground">
                        {currentAIConfig.embedding_model}
                      </span>
                    </div>
                    {currentAIConfig.base_url && (
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">API 端点：</span>
                        <span className="text-sm font-mono text-foreground truncate max-w-[200px]" title={currentAIConfig.base_url}>
                          {currentAIConfig.base_url}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-yellow-900/20 border border-yellow-800/30 rounded-lg p-4">
                    <p className="text-sm text-yellow-300">
                      未配置 AI 模型，系统将使用环境变量或默认配置
                    </p>
                  </div>
                )}

                {/* 修改配置按钮 */}
                <div className="flex justify-end">
                  <Button
                    onClick={() => setShowAIConfig(true)}
                    className="bg-purple-600 hover:bg-purple-700 text-white"
                    disabled={loadingAIConfig}
                  >
                    <SettingsIcon className="w-4 h-4 mr-2" />
                    {currentAIConfig ? '修改配置' : '配置 AI 模型'}
                  </Button>
                </div>
              </div>
            </div>

            {/* Memory Toggle */}
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="use-memory" className="text-base font-semibold text-foreground">
                    Use Memory Context
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Enable AI to remember previous interactions, preferences, and query patterns for more personalized results
                  </p>
                </div>
                <Switch
                  id="use-memory"
                  checked={useMemory}
                  onCheckedChange={setUseMemory}
                  className="data-[state=checked]:bg-purple-600"
                />
              </div>
            </div>

            {/* Database Rules Toggle */}
            <div className="bg-card p-5 rounded-lg border border-border">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="use-database-rules" className="text-base font-semibold text-foreground">
                    Use Database Rules
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Store rules in the database and use for all sessions. When disabled, rules are sent with each request
                  </p>
                </div>
                <Switch
                  id="use-database-rules"
                  checked={useRulesFromDatabase}
                  onCheckedChange={setUseRulesFromDatabase}
                  className="data-[state=checked]:bg-purple-600"
                />
              </div>
            </div>

            {/* User Rules - only show when database rules are enabled */}
            {useRulesFromDatabase && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="rules" className="text-base font-semibold text-foreground">
                    User Rules & Specifications
                  </Label>
                  <span className="text-xs text-muted-foreground">
                    {rules.length}/5000 characters
                  </span>
                </div>
              <Textarea
                id="rules"
                placeholder={`Example rules:
- Always use ISO date format (YYYY-MM-DD)
- Limit results to 100 rows unless specified
- Always include ORDER BY for consistent results
- Use LEFT JOIN instead of INNER JOIN for optional relationships
- Add comments to complex queries
- Prefer explicit column names over SELECT *
- Use descriptive aliases for clarity`}
                value={rules}
                onChange={(e) => setRules(e.target.value)}
                maxLength={5000}
                className="min-h-[400px] bg-muted border-border text-foreground placeholder:text-muted-foreground focus:border-purple-500 focus:ring-purple-500 font-mono text-sm"
              />
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setRules('')}
                  className="border-border text-muted-foreground hover:text-foreground hover:bg-muted"
                >
                  Clear
                </Button>
                {hasChanges && (
                  <Button
                    size="sm"
                    onClick={async () => {
                      if (selectedGraph?.id) {
                        try {
                          await databaseService.updateUserRules(selectedGraph.id, rules);
                          loadedRulesRef.current = rules;
                          toast({
                            title: "Saved",
                            description: "User rules saved successfully",
                          });
                        } catch (error) {
                          toast({
                            title: "Error",
                            description: error instanceof Error ? error.message : "Failed to save user rules",
                            variant: "destructive",
                          });
                        }
                      }
                    }}
                    className="bg-purple-600 hover:bg-purple-700 text-white"
                  >
                    Save
                  </Button>
                )}
              </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI 配置模态框 */}
      <AIConfigModal
        open={showAIConfig}
        onClose={() => setShowAIConfig(false)}
        onSave={handleSaveAIConfig}
        allowSkip={false}
      />
    </div>
  );
};

export default Settings;
