import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Gamepad2, Video, BarChart3, Settings, Github, Book, Coffee } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ThemeToggle';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { t } = useTranslation();
  const location = useLocation();

  const navItems = [
    { path: '/', label: t('nav.control'), icon: Gamepad2 },
    { path: '/library', label: t('nav.library'), icon: Video },
    { path: '/statistics', label: t('nav.statistics'), icon: BarChart3 },
    { path: '/config', label: t('nav.config'), icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container max-w-7xl mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <img src="/pawvision.png" alt="PawVision" className="h-8 w-8" />
            <h1 className="text-xl font-bold text-primary">
              {t('app.title')}
            </h1>
          </div>
          
          {/* External Links */}
          <div className="flex items-center gap-2">
            <ThemeToggle />
            
            <Button
              variant="ghost"
              size="icon"
              asChild
              title="GitHub Repository"
            >
              <a
                href="https://github.com/mkroemer/PawVision"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Github className="h-5 w-5" />
              </a>
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              asChild
              title="Documentation"
            >
              <a
                href="https://mkroemer.github.io/PawVision/"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Book className="h-5 w-5" />
              </a>
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              asChild
              title="Support on Ko-fi"
            >
              <a
                href="https://ko-fi.com/S6S41AWBB8"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Coffee className="h-5 w-5" />
              </a>
            </Button>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="sticky top-16 z-30 w-full border-b bg-background">
        <div className="container max-w-7xl mx-auto flex h-14 items-center px-4">
          <div className="flex w-full items-center justify-center gap-2 overflow-x-auto">
            {navItems.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={cn(
                  'inline-flex items-center gap-2 whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
                  location.pathname === path
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="container max-w-7xl mx-auto px-4 py-6 flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t py-6">
        <div className="container max-w-7xl mx-auto flex flex-col items-center justify-center gap-1 px-4 text-center text-sm text-muted-foreground">
          <div>
            © {new Date().getFullYear()} 🐾 PawVision - Made with ❤️ for pets and their humans
          </div>
          <div className="text-xs">
            <a href="https://www.gnu.org/licenses/agpl-3.0" target="_blank" rel="noopener noreferrer"> AGPL v3 License</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
