import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { buildApiUrl, API_CONFIG } from "@/config/api";
import { useState, useEffect } from "react";

interface LoginModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  canClose?: boolean; // Whether user can close the modal (false for required login)
}

interface AuthConfig {
  google: boolean;
  github: boolean;
  wechat: boolean;
  wecom: boolean;
  email: boolean;
}

const LoginModal = ({ open, onOpenChange, canClose = true }: LoginModalProps) => {
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [loading, setLoading] = useState(true);

  // 获取认证配置
  useEffect(() => {
    const fetchAuthConfig = async () => {
      try {
        const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.AUTH_STATUS), {
          credentials: 'include',
        });
        if (response.ok) {
          const data = await response.json();
          setAuthConfig(data.auth_methods || {
            google: false,
            github: false,
            wechat: false,
            wecom: false,
            email: false,
          });
        }
      } catch (error) {
        console.error('获取认证配置失败:', error);
        // 默认配置
        setAuthConfig({
          google: true,
          github: true,
          wechat: false,
          wecom: false,
          email: false,
        });
      } finally {
        setLoading(false);
      }
    };

    if (open) {
      fetchAuthConfig();
    }
  }, [open]);

  const handleGoogleLogin = () => {
    window.location.href = buildApiUrl(API_CONFIG.ENDPOINTS.LOGIN_GOOGLE);
  };

  const handleGithubLogin = () => {
    window.location.href = buildApiUrl(API_CONFIG.ENDPOINTS.LOGIN_GITHUB);
  };

  const handleWeChatLogin = () => {
    window.location.href = buildApiUrl(API_CONFIG.ENDPOINTS.LOGIN_WECHAT);
  };

  const handleWeComLogin = () => {
    window.location.href = buildApiUrl(API_CONFIG.ENDPOINTS.LOGIN_WECOM);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={canClose ? onOpenChange : undefined}
    >
      <DialogContent
        className="sm:max-w-[425px] bg-card border-border"
        onInteractOutside={(e) => {
          if (!canClose) {
            e.preventDefault();
          }
        }}
        onEscapeKeyDown={(e) => {
          if (!canClose) {
            e.preventDefault();
          }
        }}
        data-testid="login-modal"
      >
        <DialogHeader>
          <DialogTitle className="text-2xl font-semibold text-center text-card-foreground">
            欢迎使用 QueryWeaver
          </DialogTitle>
          <DialogDescription className="text-center text-muted-foreground pt-2">
            登录以访问您的数据库并开始查询
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              {authConfig?.google && (
                <Button
                  onClick={handleGoogleLogin}
                  className="w-full bg-white hover:bg-gray-50 text-gray-900 hover:text-gray-900 border-2 border-gray-300 hover:border-gray-400 font-medium py-6 text-base flex items-center justify-center gap-3 shadow-sm hover:shadow transition-all"
                  variant="outline"
                  data-testid="google-login-btn"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  使用 Google 登录
                </Button>
              )}

              {authConfig?.github && (
                <Button
                  onClick={handleGithubLogin}
                  className="w-full bg-gradient-to-r from-gray-200 to-gray-300 hover:from-gray-300 hover:to-gray-400 dark:from-[#24292e] dark:to-[#1a1e22] dark:hover:from-[#1b1f23] dark:hover:to-[#161a1d] text-gray-900 dark:text-white font-medium py-6 text-base flex items-center justify-center gap-3 shadow-md hover:shadow-lg transition-all border-2 border-gray-400 hover:border-gray-500 dark:border-gray-600"
                  data-testid="github-login-btn"
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  使用 GitHub 登录
                </Button>
              )}

              {authConfig?.wechat && (
                <Button
                  onClick={handleWeChatLogin}
                  className="w-full bg-gradient-to-r from-[#07c160] to-[#06ad56] hover:from-[#06ad56] hover:to-[#059c4d] text-white font-medium py-6 text-base flex items-center justify-center gap-3 shadow-md hover:shadow-lg transition-all border-2 border-[#06ad56] hover:border-[#059c4d]"
                  data-testid="wechat-login-btn"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8.5 9.5c0 .6-.4 1-1 1s-1-.4-1-1 .4-1 1-1 1 .4 1 1zm5 0c0 .6-.4 1-1 1s-1-.4-1-1 .4-1 1-1 1 .4 1 1zm4.5 5.5c0-.6.4-1 1-1s1 .4 1 1-.4 1-1 1-1-.4-1-1zm-3 0c0-.6.4-1 1-1s1 .4 1 1-.4 1-1 1-1-.4-1-1zM9.5 4C5.4 4 2 6.7 2 10c0 1.9 1 3.6 2.6 4.8l-.6 2.2c-.1.3.2.6.5.5l2.5-1.3c.7.2 1.4.3 2.1.3.3 0 .6 0 .9-.1-.2-.6-.3-1.2-.3-1.9 0-3.5 3.1-6.4 7-6.4.3 0 .6 0 .9.1C16.8 5.6 13.5 4 9.5 4zm12.3 9.5c0-2.8-2.8-5-6.3-5s-6.3 2.2-6.3 5 2.8 5 6.3 5c.6 0 1.2-.1 1.8-.2l2.1 1.1c.3.1.6-.2.5-.5l-.5-1.9c1.4-1 2.4-2.5 2.4-4.5z"/>
                  </svg>
                  使用微信登录
                </Button>
              )}

              {authConfig?.wecom && (
                <Button
                  onClick={handleWeComLogin}
                  className="w-full bg-gradient-to-r from-[#2e7cf6] to-[#2567d9] hover:from-[#2567d9] hover:to-[#1f5bc4] text-white font-medium py-6 text-base flex items-center justify-center gap-3 shadow-md hover:shadow-lg transition-all border-2 border-[#2567d9] hover:border-[#1f5bc4]"
                  data-testid="wecom-login-btn"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.4 0-8-3.6-8-8s3.6-8 8-8 8 3.6 8 8-3.6 8-8 8zm-1-13h2v6h-2V7zm0 8h2v2h-2v-2z"/>
                    <circle cx="8" cy="10" r="1"/>
                    <circle cx="16" cy="10" r="1"/>
                    <path d="M8 13c.6 1.2 1.8 2 3.2 2h1.6c1.4 0 2.6-.8 3.2-2H8z"/>
                  </svg>
                  使用企业微信登录
                </Button>
              )}
            </>
          )}
        </div>

        {canClose && (
          <div className="text-center text-sm text-muted-foreground pt-2">
            <p>登录即表示您同意我们的服务条款和隐私政策</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default LoginModal;
