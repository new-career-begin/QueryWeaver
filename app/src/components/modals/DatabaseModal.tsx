import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useDatabase } from "@/contexts/DatabaseContext";
import { useToast } from "@/components/ui/use-toast";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { buildApiUrl, API_CONFIG } from "@/config/api";

interface DatabaseModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ConnectionStep {
  message: string;
  status: 'pending' | 'success' | 'error';
}

const DatabaseModal = ({ open, onOpenChange }: DatabaseModalProps) => {
  const { t } = useTranslation();
  const [connectionMode, setConnectionMode] = useState<'url' | 'manual'>('url');
  const [selectedDatabase, setSelectedDatabase] = useState("");
  const [connectionUrl, setConnectionUrl] = useState("");
  const [host, setHost] = useState("localhost");
  const [port, setPort] = useState("");
  const [database, setDatabase] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionSteps, setConnectionSteps] = useState<ConnectionStep[]>([]);
  const { refreshGraphs } = useDatabase();
  const { toast } = useToast();

  const addStep = (message: string, status: 'pending' | 'success' | 'error' = 'pending') => {
    setConnectionSteps(prev => {
      // If adding a new pending step, mark the previous pending step as success
      if (status === 'pending' && prev.length > 0) {
        const lastStep = prev[prev.length - 1];
        if (lastStep.status === 'pending') {
          const updated = [...prev];
          updated[updated.length - 1] = { ...lastStep, status: 'success' };
          return [...updated, { message, status }];
        }
      }

      // If updating status (success/error), update the last pending step instead of adding new
      if (status !== 'pending' && prev.length > 0) {
        const lastStep = prev[prev.length - 1];
        if (lastStep.status === 'pending') {
          const updated = [...prev];
          updated[updated.length - 1] = { ...lastStep, status };
          return updated;
        }
      }

      // Default: just add the new step
      return [...prev, { message, status }];
    });
  };

  const handleConnect = async () => {
    // 根据连接模式验证
    if (connectionMode === 'url') {
      if (!connectionUrl || !selectedDatabase) {
        toast({
          title: t('database.messages.missingInfo'),
          description: t('database.messages.selectDatabaseAndUrl'),
          variant: "destructive",
        });
        return;
      }
    } else {
      if (!selectedDatabase || !host || !port || !database || !username) {
        toast({
          title: t('database.messages.missingInfo'),
          description: t('database.messages.fillAllFields'),
          variant: "destructive",
        });
        return;
      }
    }
    
    setIsConnecting(true);
    setConnectionSteps([]); // Clear previous steps
    
    try {
      // Build the connection URL
      let dbUrl = connectionUrl;
      if (connectionMode === 'manual') {
        const protocol = selectedDatabase === 'mysql' ? 'mysql' : 'postgresql';
        const builtUrl = new URL(`${protocol}://${host}:${port}/${database}`);
        builtUrl.username = username;
        builtUrl.password = password;
        dbUrl = builtUrl.toString();
      }

      // Make streaming request
      const response = await fetch(buildApiUrl('/database'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: dbUrl }),
        credentials: 'include',
      });

      if (!response.ok) {
        // Try to parse error message from server for all error responses
        try {
          const errorData = await response.json();
          if (errorData.error) {
            throw new Error(errorData.error);
          }
        } catch (jsonError) {
          // If JSON parsing fails, fall back to status-based messages
        }

        // Fallback error messages by status code
        const errorMessages: Record<number, string> = {
          400: t('errors.database.invalidUrl'),
          401: t('errors.auth.notAuthenticated'),
          403: t('errors.auth.accessDenied'),
          409: 'Conflict with existing database connection.',
          422: 'Invalid database connection parameters.',
          500: t('errors.network.serverError'),
        };

        throw new Error(errorMessages[response.status] || `Failed to connect to database (${response.status})`);
      }

      // Process streaming response
      if (!response.body) {
        throw new Error('Streaming response has no body');
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const delimiter = API_CONFIG.STREAM_BOUNDARY;

      const processChunk = (text: string) => {
        if (!text || !text.trim()) return;
        
        let obj: any = null;
        try {
          obj = JSON.parse(text);
        } catch (e) {
          console.error('Failed to parse chunk as JSON', e, text);
          return;
        }

        if (obj.type === 'reasoning_step') {
          // Show incremental step
          addStep(obj.message || 'Working...', 'pending');
        } else if (obj.type === 'final_result') {
          // Mark last step as success/error and finish
          addStep(obj.message || 'Completed', obj.success ? 'success' : 'error');
          setIsConnecting(false);
          
          if (obj.success) {
            toast({
              title: t('database.messages.connectedSuccessfully'),
              description: t('database.messages.databaseConnected'),
            });
            setTimeout(async () => {
              await refreshGraphs();
              onOpenChange(false);
              // 重置表单
              setConnectionMode('url');
              setSelectedDatabase("");
              setConnectionUrl("");
              setHost("localhost");
              setPort("");
              setDatabase("");
              setUsername("");
              setPassword("");
              setConnectionSteps([]);
            }, 1000);
          } else {
            toast({
              title: t('database.messages.connectionFailed'),
              description: obj.message || t('errors.network.unknownError'),
              variant: "destructive",
            });
          }
        } else if (obj.type === 'error') {
          addStep(obj.message || t('common.status.error'), 'error');
          setIsConnecting(false);
          toast({
            title: t('database.messages.connectionError'),
            description: obj.message || t('errors.network.unknownError'),
            variant: "destructive",
          });
        }
      };

      const pump = async (): Promise<void> => {
        const { done, value } = await reader.read();
        
        if (done) {
          if (buffer.length > 0) {
            processChunk(buffer);
          }
          setIsConnecting(false);
          return;
        }

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split(delimiter);
        // Last piece is possibly incomplete
        buffer = parts.pop() || '';
        for (const part of parts) {
          processChunk(part);
        }
        
        return pump();
      };

      await pump();
      
    } catch (error) {
      setIsConnecting(false);
      toast({
        title: t('database.messages.connectionFailed'),
        description: error instanceof Error ? error.message : t('database.messages.connectionFailed'),
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto bg-card border-border">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold text-card-foreground">
            {t('database.modal.title')}
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {t('database.modal.description')}{" "}
            <a
              href="https://www.falkordb.com/privacy-policy/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              {t('database.modal.privacyPolicy')}
            </a>
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 mt-6" data-testid="database-modal-content">
          {/* 数据库类型选择 */}
          <div className="space-y-2">
            <Label htmlFor="database-type" className="text-sm font-medium">
              {t('database.fields.databaseType')}
            </Label>
            <Select onValueChange={setSelectedDatabase} value={selectedDatabase}>
              <div data-testid="database-type-select">
                <SelectTrigger className="bg-muted border-border focus:ring-purple-500">
                  <SelectValue placeholder={t('database.fields.selectDatabase')} />
                </SelectTrigger>
              </div>
              <SelectContent className="bg-card border-border">
                <SelectItem value="postgresql" className="focus:bg-purple-500/20 focus:text-foreground" data-testid="postgresql-option">
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-blue-500 rounded-sm mr-2"></div>
                    {t('database.types.postgresql')}
                  </div>
                </SelectItem>
                <SelectItem value="mysql" className="focus:bg-purple-500/20 focus:text-foreground" data-testid="mysql-option">
                  <div className="flex items-center">
                    <div className="w-4 h-4 bg-orange-500 rounded-sm mr-2"></div>
                    {t('database.types.mysql')}
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* 连接模式切换 */}
          {selectedDatabase && (
            <div className="flex gap-2 p-1 bg-muted rounded-lg">
              <Button
                type="button"
                variant={connectionMode === 'url' ? 'default' : 'ghost'}
                className={`flex-1 ${connectionMode === 'url' ? 'bg-purple-600 hover:bg-purple-700' : ''}`}
                onClick={() => setConnectionMode('url')}
                data-testid="connection-mode-url"
              >
                {t('database.modes.url')}
              </Button>
              <Button
                type="button"
                variant={connectionMode === 'manual' ? 'default' : 'ghost'}
                className={`flex-1 ${connectionMode === 'manual' ? 'bg-purple-600 hover:bg-purple-700' : ''}`}
                onClick={() => setConnectionMode('manual')}
                data-testid="connection-mode-manual"
              >
                {t('database.modes.manual')}
              </Button>
            </div>
          )}

          {selectedDatabase && connectionMode === 'url' && (
            <div className="space-y-2">
              <Label htmlFor="connection-url" className="text-sm font-medium">
                {t('database.fields.connectionUrl')}
              </Label>
              <Input
                id="connection-url"
                data-testid="connection-url-input"
                placeholder={
                  selectedDatabase === 'postgresql'
                    ? 'postgresql://username:password@host:5432/database'
                    : 'mysql://username:password@host:3306/database'
                }
                value={connectionUrl}
                onChange={(e) => setConnectionUrl(e.target.value)}
                className="bg-muted border-border font-mono text-sm focus-visible:ring-purple-500"
              />
              <p className="text-xs text-muted-foreground">
                {t('database.fields.enterConnectionString')}
              </p>
            </div>
          )}

          {selectedDatabase && connectionMode === 'manual' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="host" className="text-sm font-medium">{t('database.fields.host')}</Label>
                <Input
                  id="host"
                  placeholder="localhost"
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  className="bg-muted border-border focus-visible:ring-purple-500"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="port" className="text-sm font-medium">{t('database.fields.port')}</Label>
                <Input
                  id="port"
                  placeholder={selectedDatabase === "postgresql" ? "5432" : "3306"}
                  value={port}
                  onChange={(e) => setPort(e.target.value)}
                  className="bg-muted border-border focus-visible:ring-purple-500"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="database" className="text-sm font-medium">{t('database.fields.database')}</Label>
                <Input
                  id="database"
                  placeholder="my_database"
                  value={database}
                  onChange={(e) => setDatabase(e.target.value)}
                  className="bg-muted border-border focus-visible:ring-purple-500"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="username" className="text-sm font-medium">{t('database.fields.username')}</Label>
                <Input
                  id="username"
                  placeholder="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="bg-muted border-border focus-visible:ring-purple-500"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium">{t('database.fields.password')}</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="bg-muted border-border focus-visible:ring-purple-500"
                />
              </div>
            </>
          )}

          {/* 连接进度步骤 */}
          {connectionSteps.length > 0 && (
            <div className="mt-4 space-y-2 max-h-[220px] overflow-y-auto border border-border rounded-md p-3 bg-muted/30">
              {connectionSteps.map((step, index) => (
                <div key={index} className="flex items-start gap-2 text-sm">
                  {step.status === 'pending' && (
                    <Loader2 className="w-4 h-4 mt-0.5 text-blue-500 animate-spin flex-shrink-0" />
                  )}
                  {step.status === 'success' && (
                    <CheckCircle2 className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                  )}
                  {step.status === 'error' && (
                    <XCircle className="w-4 h-4 mt-0.5 text-red-500 flex-shrink-0" />
                  )}
                  <span className={`flex-1 ${
                    step.status === 'error' ? 'text-red-400' : 'text-card-foreground'
                  }`}>
                    {step.message}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-3 mt-6">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isConnecting}
            className="hover:bg-purple-500/20 hover:text-foreground"
            data-testid="cancel-database-button"
          >
            {t('common.buttons.cancel')}
          </Button>
          <Button
            onClick={handleConnect}
            disabled={!selectedDatabase || isConnecting}
            className="bg-purple-600 hover:bg-purple-700"
            data-testid="connect-database-button"
          >
            {isConnecting ? t('database.messages.connecting') : t('common.buttons.connect')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DatabaseModal;